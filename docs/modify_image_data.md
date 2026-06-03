# Modifying Image Data

How authenticated users edit image data, what gets recorded, and how to keep the
derived `Calculation` data consistent afterwards.

## 1. The edit UI (project detail page)

Images are edited from the edit modal on `project/details/<pk>/`
(`taicat/templates/project/project_detail.html`, posting to
`edit_image` → `taicat/views.py`).

### Editable vs. locked fields

Only the **annotation** of an image may be edited. The **structural** fields
(when / where) are locked in the UI:

| Field | 中文 | Editable? | How it is locked |
|-------|------|-----------|------------------|
| species | 物種 | ✅ yes | — |
| life_stage | 年齡 | ✅ yes | — |
| sex | 性別 | ✅ yes | — |
| antler | 角況 | ✅ yes | — |
| animal_id | 個體ID | ✅ yes | — |
| remarks | 備註 | ✅ yes | — |
| date | 日期 | ❌ no | `disabled` + gray (`static/js/project_detail.js`) |
| time | 時間 | ❌ no | `disabled` + gray |
| project | 計畫 | ❌ no | `disabled` + gray |
| studyarea | 樣區 | ❌ no | `readonly` (template) |
| deployment | 相機位置 | ❌ no | `readonly` (template) |

Implementation notes:

- `studyarea` / `deployment` are `readonly` inputs with no focus handler, so they
  cannot be typed into or opened.
- `date` / `time` / `project` are re-`disabled` in `project_detail.js` whenever
  edit mode is entered, and the date-picker (`.edit-date-cal`) is kept hidden, so
  the AirDatepicker / autocomplete cannot write a value programmatically.
- Gray-out styling lives in `static/css/project_detail.css`
  (`#edit-studyarea[readonly]`, `#edit-date:disabled`, …).

> ⚠️ This is a **UI-only** restriction. The `edit_image` view still accepts these
> fields if posted directly. If server-side enforcement is needed, add a check in
> the view.

## 2. Audit trail — `ModifiedImage`

Every edit that actually changes a value is logged to `taicat_modifiedimage`
(`taicat/models.py` → `ModifiedImage`). For each changed image one row stores:

- **who**: `contact_id` (from the logged-in session)
- **which**: `image_id`, `project_id`, `studyarea_id`
- **when**: `last_updated` (a `DateField` — **date only**, no time)
- **before**: `species`, `life_stage`, `sex`, `antler`, `animal_id`, `remarks`,
  `datetime`, `project`, `studyarea`, `deployment`
- **after**: the same fields prefixed `modified_*`

A row is written only when `before != after`
(`taicat/views.py`, `ModifiedImage.objects.bulk_create(...)`).

There is currently **no UI** to view this history; query the table directly.

## 3. Recalculating `Calculation` after edits

Editing an image does **not** refresh the derived `Calculation` rows. Several
operations leave `Calculation` stale and need a recalc:

| Operation | Logs to ModifiedImage? | Recalc tool |
|-----------|------------------------|-------------|
| Edit species via UI (`edit_image`) | ✅ yes | `scripts/recalc-modified-images.py` |
| `scripts/swap-deployment.py` | ❌ no | `scripts/recalc-deployment.py` (both source & target) |
| `scripts/delete_upload_folder.py` | ❌ no | `scripts/recalc-deployment.py` (the folder's deployment) |

All recalc paths reuse helpers in `taicat/utils.py`:
`recalc_deployment_month`, `prune_orphan_calculations`, `recalc_deployment`
(which build on the existing `save_calculation` / `Deployment.calculate`).

### Cell model

A `Calculation` row is keyed by `(deployment, datetime_from, species,
image_interval, event_interval)`. `datetime_from` is the **Taiwan-local** month
start stored in UTC (e.g. `2024-01` → `2023-12-31 16:00Z`), because
`Deployment.calculate()` defines each month window in TW time. An image therefore
belongs to the calculation cell of its **TW month**.

### Zero-baseline rows (important)

The data intentionally keeps a **zero-count** `Calculation` row for a species in
months it is absent, as long as that species appears somewhere in the deployment
(and always for `Species.DEFAULT_LIST` species). These zero rows are **not**
stale and must not be deleted — the analysis relies on them to show "0
detections" for a month.

Consequently the recalc logic:

- **Recomputes** every species that has images *or* an existing row in a cell —
  present species get correct counts, absent species are recomputed to `0`.
- **Prunes** only *true orphans*: a **non-default** species that has a
  `Calculation` row but **no image anywhere in the deployment** (e.g. a typo such
  as `野野山羊` that was corrected to `野山羊` by edits). Default species and
  species still present in other months keep their zero baselines.

### `scripts/recalc-modified-images.py`

Recompute the cells touched by edits logged on/after a date.

```bash
# preview
python scripts/recalc-modified-images.py --start-date 2026-01-01 --dry-run
# apply
python scripts/recalc-modified-images.py --start-date 2026-01-01
```

- Finds `ModifiedImage` with `last_updated >= --start-date`.
- Maps each edit to its current `(deployment, TW-year, TW-month)` cell and
  recomputes that cell. It does **not** prune deployment-wide orphans; run
  `recalc-deployment.py` for that.
- `--start-date` is required; `--dry-run` previews without writing.
- Note: one `Image` lookup per edit (N+1). Fine for incremental runs; for a large
  backfill keep the start date recent.

### `scripts/recalc-deployment.py`

Full reconcile of one or more deployments: recompute all cells **and** prune
orphan species.

```bash
# after a swap from 13909 to 14001
python scripts/recalc-deployment.py --from-deployment 13909 --to-deployment 14001
# after deleting a folder whose images were on deployment 13896 (preview)
python scripts/recalc-deployment.py --deployment-id 13896 --dry-run
# limit to one year
python scripts/recalc-deployment.py --deployment-id 13896 --year 2024
```

- `--deployment-id` is repeatable; `--from-deployment` / `--to-deployment` are
  conveniences for a swap. All given deployments are processed.
- `--year` limits both recompute and prune to a single year (orphan species are
  identified deployment-wide, but only that year's rows are deleted).
- `--dry-run` reports the prune list (species + row count) and the per-cell
  recompute lists without writing.

> Scope: these tools fix **`Calculation`** only. `delete_upload_folder.py` also
> leaves `ProjectStat`, `ProjectSpecies`, `Species`, `ImageFolder` and
> `DeploymentStat` stale; those need separate handling.

## 4. Related code

- Edit form / UI: `taicat/templates/project/project_detail.html`,
  `static/js/project_detail.js`, `static/css/project_detail.css`
- Edit view: `edit_image` in `taicat/views.py`
- Audit model: `ModifiedImage` in `taicat/models.py`
- Calculation: `Deployment.calculate` in `taicat/models.py`,
  `save_calculation` / `recalc_deployment*` in `taicat/utils.py`
- See also: [`calculation.md`](calculation.md), [`scripts.md`](scripts.md)
