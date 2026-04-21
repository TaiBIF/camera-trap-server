"""Read-only DuckDB access helpers."""
import os
import threading
from contextlib import contextmanager

import duckdb

DUCKDB_PATH = os.environ.get('DUCKDB_PATH', '/data/cameratrap.duckdb')

_lock = threading.Lock()


@contextmanager
def connect():
    """Open a read-only connection to the snapshot file.

    DuckDB supports multiple read-only connections, but we serialize here
    anyway so slow queries can't overlap and starve the bot's event loop.
    """
    with _lock:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        try:
            yield con
        finally:
            con.close()


def query(sql: str, params: tuple = ()):
    with connect() as con:
        return con.execute(sql, params).fetchall()


def snapshot_info() -> dict | None:
    try:
        row = query(
            'SELECT run_at, duration_sec, row_counts_json '
            'FROM etl_metadata ORDER BY run_at DESC LIMIT 1;'
        )
    except duckdb.Error:
        return None
    if not row:
        return None
    run_at, duration, counts = row[0]
    return {'run_at': run_at, 'duration_sec': duration, 'row_counts_json': counts}
