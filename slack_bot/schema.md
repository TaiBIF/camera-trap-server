# Camera Trap DuckDB Schema

The database is a weekly snapshot of a Django PostgreSQL wildlife camera-trap
system. All species names are in Traditional Chinese (zh-TW). Timestamps are
stored in UTC; the project operates in Taiwan (UTC+8).

## Tables

### project
Research projects. One project owns many studyareas and many deployments.

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | 計畫名稱 (full name) |
| short_title | TEXT | 計畫簡稱 |
| description | TEXT | 計畫摘要 |
| keyword | TEXT | search keywords |
| start_date | DATE | |
| end_date | DATE | |
| executive_unit | TEXT | 執行單位 |
| principal_investigator | TEXT | 計畫主持人 |
| funding_agency | TEXT | 委辦單位 |
| region | TEXT | 計畫地區 |
| mode | TEXT | 'official' or 'test' — filter `mode = 'official'` for real projects |
| is_public | BOOLEAN | |
| publish_date | DATE | |

### studyarea
Named survey regions within a project. Hierarchical (parent_id self-reference).

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | |
| parent_id | INTEGER | self FK; NULL for top-level |
| project_id | INTEGER FK → project.id | |

### deployment
Individual camera trap locations. One studyarea has many deployments.

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | 相機位置名稱 |
| project_id | INTEGER FK → project.id | |
| study_area_id | INTEGER FK → studyarea.id | NOTE: column is `study_area_id` not `studyarea_id` |
| longitude | DECIMAL | |
| latitude | DECIMAL | |
| altitude | SMALLINT | |
| geodetic_datum | TEXT | 'TWD97' or 'WGS84' |
| county | TEXT | 縣市 code — join taicat_parametercode if translating |
| protectedarea | TEXT | 國家公園/保護留區 code |
| landcover | TEXT | 土地覆蓋 |
| vegetation | TEXT | 植被類型 |
| camera_status | TEXT | '1'=正常, '2'-'6'=各種故障/失竊 |
| deprecated | BOOLEAN | skip when TRUE |

### image
Individual wildlife photos. Biggest table (tens of millions of rows).
Only a projection of relevant columns is in the snapshot (no annotation JSON,
no raw EXIF, no thumbnails).

| column | type | notes |
|---|---|---|
| id | BIGINT PK | |
| project_id | INTEGER | |
| deployment_id | INTEGER | |
| studyarea_id | INTEGER | |
| deployment_journal_id | INTEGER | |
| species | TEXT | 中文俗名 e.g. '水鹿', '山羌', '台灣黑熊'; empty string or NULL = unidentified |
| life_stage | TEXT | 生命階段 e.g. '成體', '幼體' |
| sex | TEXT | '雄', '雌', '' |
| antler | TEXT | rack/antler status |
| animal_id | TEXT | individual animal ID when known |
| datetime | TIMESTAMP | when photo was captured (UTC) |
| folder_name | TEXT | uploader batch name |
| image_uuid | TEXT | |
| has_storage | TEXT | 'Y' if S3 file present, 'N' otherwise |
| is_duplicated | TEXT | '', 'Y', ... |

Common species values worth knowing: 水鹿, 山羌, 獼猴, 野山羊, 野豬, 鼬獾,
白鼻心, 食蟹獴, 松鼠, 飛鼠, 黃喉貂, 黃鼠狼, 小黃鼠狼, 麝香貓, 黑熊 (aka 台灣黑熊),
石虎, 穿山甲, 梅花鹿, 野兔, 蝙蝠.

Non-wildlife labels to usually exclude from species queries unless the user
asks about them explicitly: 人, 人（有槍）, 人＋狗, 狗＋人, 獵人, 砍草工人,
研究人員, 研究人員自己, 除草工人.

### species
Master species list with global counts.

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | |
| count | INTEGER | cached total image count |
| is_default | BOOLEAN | is on the standard 20-species list |
| last_updated | TIMESTAMP | |

### deploymentjournal
Camera working periods. Each row = one continuous working interval for a
deployment. Use to compute camera-hours / effective survey days.

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER | |
| deployment_id | INTEGER | |
| studyarea_id | INTEGER | |
| working_start | TIMESTAMP | |
| working_end | TIMESTAMP | |
| is_effective | BOOLEAN | TRUE = camera actually recording |
| is_gap | BOOLEAN | TRUE = confirmed data gap |
| gap_caused | TEXT | |

### calculation
Pre-computed wildlife density indices (OI1/OI2/OI3) per deployment × species ×
year × month, for several `image_interval` / `event_interval` combinations.

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER | |
| studyarea_id | INTEGER | |
| deployment_id | INTEGER | |
| datetime_from | TIMESTAMP | |
| datetime_to | TIMESTAMP | |
| species | TEXT | |
| image_interval | SMALLINT | minutes — usually 30 or 60 |
| event_interval | SMALLINT | minutes — usually 2, 5, 10, 30, 60 |
| data | JSON | see structure below |

`calculation.data` JSON typically contains keys like `oi1`, `oi2`, `oi3`,
`num_images`, `num_events`, `working_hours`. To extract a number:
`CAST(json_extract(data, '$.oi3') AS DOUBLE)`. When in doubt, pick
`image_interval=30 AND event_interval=5` as defaults.

### deploymentstat, projectstat, projectspecies, homepagestat, geostat, studyareastat
Pre-aggregated convenience tables. Generally useful for fast summaries.

- `projectstat(project_id, num_sa, num_deployment, num_data, earliest_date, latest_date, last_updated)`
- `projectspecies(project_id, name, count, last_updated)` — species × project counts
- `deploymentstat(deployment_id, count_working_hour, ...)` — per-deployment totals
- `geostat(county, num_project, num_deployment, num_image, num_working_hour, identified, species, studyarea)` — per-county rollup
- `homepagestat(year, count, last_updated)` — yearly cumulative image counts

### contact, organization
User accounts & organizations. Usually not needed for analytics.

## Convenience views

Already defined in the snapshot:

- `v_project_summary(project_id, project_name, short_title, funding_agency,
  start_date, end_date, mode, is_public, n_deployments, n_studyareas,
  n_images, n_species, first_image_at, last_image_at)` — one row per project.
- `v_species_by_project(project_id, project_name, species, n_images,
  first_seen, last_seen)` — species counts per project (excludes
  NULL/empty species).
- `v_species_total(species, n_images)` — global species counts, sorted.

## Query rules

1. Return exactly **one** `SELECT` (or `WITH ... SELECT`) statement. No DDL,
   DML, PRAGMA, ATTACH, COPY, LOAD, INSTALL, CREATE, DROP, ALTER, UPDATE,
   INSERT, DELETE, REPLACE, EXPORT, IMPORT, VACUUM, CHECKPOINT. The query
   runs in a read-only connection.
2. Always add `LIMIT` (≤ 500). If the user asks for "all", cap at 500 anyway.
3. For species matching, use `ILIKE` with wildcards so users can search
   "黑熊" and match "台灣黑熊": `species ILIKE '%黑熊%'`.
4. When filtering projects by name, search both `name` and `short_title`
   with `ILIKE`.
5. When grouping by time, extract parts with `date_part('year', datetime)`
   and `date_part('month', datetime)`.
6. When comparing to "now" or "recent", use `CURRENT_DATE` / `NOW()`.
7. Prefer the convenience views and pre-aggregated tables when possible —
   they are much faster than scanning `image`.
8. Exclude rows with `species IS NULL OR species = ''` when answering
   species-level questions, unless the user specifically asked about
   unidentified photos.
9. Exclude `project.mode = 'test'` when answering questions about "all
   projects" or producing global numbers, unless the user asks for tests.
