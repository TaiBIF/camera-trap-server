# Camtrap DP Export — `scripts/export-camtrap-dp.py`

Export TaiCAT project data to **Camera Trap Data Package (Camtrap DP) 1.0** — the TDWG-endorsed exchange format. One Frictionless data package per project.

Spec: https://camtrap-dp.tdwg.org/

## Usage

```bash
# single project
python scripts/export-camtrap-dp.py --project-id 287

# multiple projects, custom output dir
python scripts/export-camtrap-dp.py --project-id 287,288 -o /tmp/dp

# every published project
python scripts/export-camtrap-dp.py --all-published
```

## Output layout

```
<output>/
└── project-<id>-<slug>/
    ├── datapackage.json     # Frictionless descriptor + Camtrap DP metadata
    ├── deployments.csv
    ├── media.csv
    └── observations.csv
```

## Model → Camtrap mapping

| Camtrap DP resource | Source                                      | Key field                                  |
|---------------------|---------------------------------------------|--------------------------------------------|
| deployment          | `DeploymentJournal` (effective, non-gap)    | `deploymentID = j-<journal.id>`            |
| location            | `Deployment`                                | `locationID = loc-<deployment.id>`         |
| media               | `Image` (excluding `is_duplicated='Y'`)     | `mediaID = image_uuid` or `img-<id>`       |
| observation         | `Image` at `observationLevel = media`       | `observationID = obs-<image.id>`           |

Each `DeploymentJournal` becomes one Camtrap deployment row (a continuous camera operation period at a location), matching the spec's "camera at a specific location for a specific period of time."

## Caveats

- **Timestamps.** `Image.datetime` is UTC → shifted to `+08:00`. `DeploymentJournal.working_start/end` is naive Taipei time → tagged `+08:00` without shifting (matches the comment in `taicat/models.py:500`).
- **Species names** are written as-is (Chinese) into `scientificName`. No Latin-name resolution. Blank species → `observationType = blank`.
- **Images without `deployment_journal_id`** are skipped — they can't be tied to a Camtrap deployment.
- **Licenses** map `cc0`/`by`/`by-nc` → `CC0-1.0` / `CC-BY-4.0` / `CC-BY-NC-4.0`. Falls back to `CC-BY-4.0` if the project has no license set.

## Tags

#camera-trap #camtrap-dp #tdwg #export #taicat
