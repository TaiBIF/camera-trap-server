"""Weekly ETL: PostgreSQL -> DuckDB snapshot for the Slack analytics bot.

Run via:
    python ./manage.py shell < ./cron_scripts/duckdb_etl.py

Uses DuckDB's built-in ``postgres`` extension (formerly ``postgres_scanner``)
to stream projected tables from the live Postgres database into a single
DuckDB file. The file is written to /duckdb/cameratrap.duckdb inside the
container (mounted from ../ct22-volumes/duckdb on the host) so the slack_bot
service can read it via a read-only bind mount.
"""
import json
import os
import time
from datetime import datetime

import duckdb


DUCKDB_PATH = os.environ.get('DUCKDB_PATH', '/duckdb/cameratrap.duckdb')

PG = {
    'host': os.environ.get('POSTGRES_HOST', 'postgres'),
    'port': os.environ.get('POSTGRES_PORT', '5432'),
    'dbname': os.environ.get('POSTGRES_DB', 'cameratrap'),
    'user': os.environ.get('POSTGRES_USER', 'postgres'),
    'password': os.environ.get('POSTGRES_PASSWORD', ''),
}

# Tables copied whole (small reference tables).
FULL_TABLES = [
    'taicat_project',
    'taicat_studyarea',
    'taicat_deployment',
    'taicat_species',
    'taicat_projectspecies',
    'taicat_projectstat',
    'taicat_deploymentstat',
    'taicat_deploymentjournal',
    'taicat_calculation',
    'taicat_contact',
    'taicat_organization',
    'taicat_geostat',
    'taicat_studyareastat',
    'taicat_homepagestat',
]

# taicat_image is huge: project to the columns the bot actually needs.
# Everything dropped here (annotation, remarks2, source_data, memo, image_hash,
# EXIF-like fields) would dominate DB size without helping analytics queries.
IMAGE_COLUMNS = [
    'id',
    'project_id',
    'deployment_id',
    'studyarea_id',
    'deployment_journal_id',
    'species',
    'life_stage',
    'sex',
    'antler',
    'animal_id',
    'datetime',
    'folder_name',
    'image_uuid',
    'has_storage',
    'is_duplicated',
    'created',
    'last_updated',
]


def strip_prefix(table: str) -> str:
    return table[len('taicat_'):] if table.startswith('taicat_') else table


def attach_postgres(con):
    dsn = (
        f"host={PG['host']} port={PG['port']} dbname={PG['dbname']} "
        f"user={PG['user']} password={PG['password']}"
    )
    con.execute('INSTALL postgres;')
    con.execute('LOAD postgres;')
    con.execute(f"ATTACH '{dsn}' AS pg (TYPE POSTGRES, READ_ONLY);")


def copy_table(con, pg_table: str, columns: str = '*') -> int:
    local = strip_prefix(pg_table)
    con.execute(f'DROP TABLE IF EXISTS {local};')
    con.execute(
        f'CREATE TABLE {local} AS SELECT {columns} FROM pg.public.{pg_table};'
    )
    return con.execute(f'SELECT COUNT(*) FROM {local};').fetchone()[0]


def build_views(con):
    con.execute('''
        CREATE OR REPLACE VIEW v_project_summary AS
        SELECT
            p.id                                AS project_id,
            p.name                              AS project_name,
            p.short_title,
            p.funding_agency,
            p.start_date,
            p.end_date,
            p.mode,
            p.is_public,
            COUNT(DISTINCT d.id)                AS n_deployments,
            COUNT(DISTINCT s.id)                AS n_studyareas,
            COUNT(i.id)                         AS n_images,
            COUNT(DISTINCT NULLIF(i.species,'')) AS n_species,
            MIN(i.datetime)                     AS first_image_at,
            MAX(i.datetime)                     AS last_image_at
        FROM project p
        LEFT JOIN deployment d ON d.project_id = p.id
        LEFT JOIN studyarea  s ON s.project_id = p.id
        LEFT JOIN image      i ON i.project_id = p.id
        GROUP BY p.id, p.name, p.short_title, p.funding_agency,
                 p.start_date, p.end_date, p.mode, p.is_public;
    ''')
    con.execute('''
        CREATE OR REPLACE VIEW v_species_by_project AS
        SELECT
            i.project_id,
            p.name     AS project_name,
            i.species,
            COUNT(*)   AS n_images,
            MIN(i.datetime) AS first_seen,
            MAX(i.datetime) AS last_seen
        FROM image i
        JOIN project p ON p.id = i.project_id
        WHERE i.species IS NOT NULL AND i.species <> ''
        GROUP BY i.project_id, p.name, i.species;
    ''')
    con.execute('''
        CREATE OR REPLACE VIEW v_species_total AS
        SELECT species, COUNT(*) AS n_images
        FROM image
        WHERE species IS NOT NULL AND species <> ''
        GROUP BY species
        ORDER BY n_images DESC;
    ''')


def record_metadata(con, counts: dict, started_at: float):
    con.execute('''
        CREATE TABLE IF NOT EXISTS etl_metadata (
            run_at          TIMESTAMP,
            source_host     TEXT,
            source_db       TEXT,
            duration_sec    DOUBLE,
            row_counts_json TEXT
        );
    ''')
    con.execute(
        'INSERT INTO etl_metadata VALUES (?, ?, ?, ?, ?);',
        [
            datetime.utcnow(),
            PG['host'],
            PG['dbname'],
            time.time() - started_at,
            json.dumps(counts, default=str),
        ],
    )


def run():
    started = time.time()
    print(f'[duckdb_etl] writing snapshot to {DUCKDB_PATH}')
    os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)

    con = duckdb.connect(DUCKDB_PATH)
    attach_postgres(con)

    counts: dict = {}
    for table in FULL_TABLES:
        try:
            n = copy_table(con, table)
        except duckdb.Error as exc:
            print(f'[duckdb_etl] skip {table}: {exc}')
            continue
        counts[strip_prefix(table)] = n
        print(f'[duckdb_etl] {table:32s} {n:>10,} rows')

    counts['image'] = copy_table(con, 'taicat_image', ', '.join(IMAGE_COLUMNS))
    print(f"[duckdb_etl] taicat_image                    {counts['image']:>10,} rows")

    con.execute('CREATE INDEX IF NOT EXISTS idx_image_project   ON image(project_id);')
    con.execute('CREATE INDEX IF NOT EXISTS idx_image_deploy    ON image(deployment_id);')
    con.execute('CREATE INDEX IF NOT EXISTS idx_image_species   ON image(species);')
    con.execute('CREATE INDEX IF NOT EXISTS idx_image_datetime  ON image(datetime);')

    build_views(con)
    record_metadata(con, counts, started)
    con.execute('DETACH pg;')
    con.close()

    print(f'[duckdb_etl] done in {time.time() - started:.1f}s')


run()
