"""
Camtrap DP 資料包基本分析：物種紀錄數、相機工作時數、OI3、出現樣點比例、活動時段。

用法：
    pip install duckdb
    python camtrap_analysis.py <資料包資料夾> [輸出資料夾]

輸出（UTF-8 BOM，可直接用 Excel 開啟）：
    species_summary.csv    各物種紀錄數、獨立有效照片數、出現樣點數
    effort_by_location.csv 各相機位置的工作天數與工作時數
    oi3_by_location.csv    各相機位置 × 物種的 OI3
    activity_by_hour.csv   各物種 0–23 時的獨立有效照片數
"""

import csv
import json
import sys
from pathlib import Path

import duckdb

IMAGE_INTERVAL_MIN = 60           # 獨立有效照片的間隔門檻（分鐘）
EXCLUDE_TIMESTAMP_ISSUES = True   # 排除 timestampIssues = true 的相機期間
BBOX = (21.5, 26.5, 118.0, 123.5) # 臺灣範圍：緯度下限、上限、經度下限、上限


def write_csv(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main(pkg, out):
    pkg, out = Path(pkg), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    # 所有欄位先以文字讀入：時間已是 +08:00，直接取字串前 10 碼為日期、第 12–13 碼為小時
    con.execute(f"""
        CREATE VIEW deployments AS
        SELECT * FROM read_csv('{pkg / 'deployments.csv'}', header=true, all_varchar=true)
    """)
    con.execute(f"""
        CREATE VIEW observations AS
        SELECT * FROM read_csv('{pkg / 'observations.csv'}', header=true, all_varchar=true)
    """)

    lat_min, lat_max, lon_min, lon_max = BBOX
    ts_filter = "AND timestampIssues = 'false'" if EXCLUDE_TIMESTAMP_ISSUES else ''
    con.execute(f"""
        CREATE TABLE good_deployments AS
        SELECT deploymentID, locationID, locationName,
               CAST(latitude AS DOUBLE) AS latitude, CAST(longitude AS DOUBLE) AS longitude,
               CAST(left(deploymentStart, 10) AS DATE) AS start_date,
               CAST(left(deploymentEnd, 10) AS DATE) AS end_date
        FROM deployments
        WHERE CAST(latitude AS DOUBLE) BETWEEN {lat_min} AND {lat_max}
          AND CAST(longitude AS DOUBLE) BETWEEN {lon_min} AND {lon_max}
          {ts_filter}
    """)

    # 相機工作天數：同一位置各期間涵蓋的日期取聯集（重疊不重複計算），工作時數 = 天數 × 24
    effort = con.execute("""
        WITH days AS (
            SELECT DISTINCT locationID,
                   unnest(generate_series(start_date, end_date, INTERVAL 1 DAY)) AS day
            FROM good_deployments
        )
        SELECT d.locationID, any_value(g.locationName), any_value(g.latitude),
               any_value(g.longitude), count(DISTINCT d.day) AS working_days,
               count(DISTINCT d.day) * 24 AS working_hours
        FROM days d JOIN good_deployments g USING (locationID)
        GROUP BY d.locationID ORDER BY d.locationID
    """).fetchall()
    write_csv(out / 'effort_by_location.csv',
              ['locationID', 'locationName', 'latitude', 'longitude',
               'working_days', 'working_hours'], effort)
    hours_by_loc = {r[0]: r[5] for r in effort}

    # 動物照片（有學名），依位置、物種、時間排序
    rows = con.execute("""
        SELECT g.locationID, o.scientificName, o.eventStart
        FROM observations o JOIN good_deployments g USING (deploymentID)
        WHERE o.observationType = 'animal' AND o.scientificName IS NOT NULL
        ORDER BY g.locationID, o.scientificName, o.eventStart
    """)

    # 獨立有效照片：與上一張「計入」的照片相隔 >= IMAGE_INTERVAL_MIN 才算新的一張
    threshold = IMAGE_INTERVAL_MIN * 60
    from datetime import datetime
    records = {}      # species -> 紀錄數
    independent = {}  # (location, species) -> 獨立有效照片數
    by_hour = {}      # (species, hour) -> 獨立有效照片數
    key = last_counted = None
    while batch := rows.fetchmany(100_000):
        for loc, sp, ts in batch:
            records[sp] = records.get(sp, 0) + 1
            t = datetime.fromisoformat(ts)
            if (loc, sp) != key:
                key, last_counted = (loc, sp), None
            if last_counted is None or (t - last_counted).total_seconds() >= threshold:
                last_counted = t
                independent[key] = independent.get(key, 0) + 1
                by_hour[(sp, t.hour)] = by_hour.get((sp, t.hour), 0) + 1

    # 中文名與 TaiCOL 編號取自 datapackage.json
    meta = json.loads((pkg / 'datapackage.json').read_text(encoding='utf-8'))
    taxa = {t['scientificName']: t for t in meta.get('taxonomic', [])}

    n_locations = len(hours_by_loc)
    species_rows = []
    for sp, n in records.items():
        locs = [loc for (loc, s) in independent if s == sp]
        species_rows.append([
            sp, taxa.get(sp, {}).get('vernacularNames', {}).get('zho', ''),
            taxa.get(sp, {}).get('taxonID', ''), n,
            sum(independent[(loc, sp)] for loc in locs), len(locs),
            round(len(locs) / n_locations, 4) if n_locations else '',
        ])
    species_rows.sort(key=lambda r: -r[4])
    write_csv(out / 'species_summary.csv',
              ['scientificName', 'vernacularName', 'taxonID', 'records',
               'independent_photos', 'locations_detected', 'naive_occupancy'],
              species_rows)

    oi3_rows = []
    for (loc, sp), n in sorted(independent.items()):
        hours = hours_by_loc.get(loc, 0)
        oi3_rows.append([loc, sp, n, hours, round(n / hours * 1000, 4) if hours else ''])
    write_csv(out / 'oi3_by_location.csv',
              ['locationID', 'scientificName', 'independent_photos', 'working_hours', 'OI3'],
              oi3_rows)

    write_csv(out / 'activity_by_hour.csv', ['scientificName', 'hour', 'independent_photos'],
              [[sp, h, n] for (sp, h), n in sorted(by_hour.items())])

    print(f'image interval: {IMAGE_INTERVAL_MIN} min; locations: {n_locations}; '
          f'species: {len(records)}; output: {out}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('用法：python camtrap_analysis.py <資料包資料夾> [輸出資料夾]')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'analysis-output')
