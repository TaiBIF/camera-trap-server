# Calculating OI1 / OI2 / OI3 / POD from a Camtrap DP dataset

This note explains the relative-abundance indices TaiCAT reports and shows how to
recompute them **from an exported Camtrap DP package** (the directory produced by
[`scripts/export-camtrap-dp.py`](../scripts/export-camtrap-dp.py)) instead of from
the live database.

The reference implementation is
[`Deployment.calculate`](../taicat/models.py) in `taicat/models.py`. The formulas
below are the same; only the *data source* changes — from the Django ORM to the
three CSV files (`deployments.csv`, `media.csv`, `observations.csv`).

---

## 1. What the indices mean

All three "OI" (Occurrence Index / 相對豐富度指數) values share the same shape:

```
OI = (independent_capture_count / effective_camera_hours) × 1000
```

i.e. **independent captures of a species per 1 000 camera-working-hours**. They
differ only in *how an "independent capture" is counted*:

| Index | Counting rule | Uses individual ID? |
|-------|---------------|---------------------|
| **OI1** | New capture when the animal individual changes, **or** the same individual reappears after `image_interval` | Yes (`individualID` / `animal_id`) |
| **OI2** | New capture whenever the gap since the last counted photo ≥ `image_interval` (purely time-based, individual ignored) | No |
| **OI3** | Same time-based rule as OI2, applied to photos that have **no** individual ID | No |

`POD` is a different kind of metric:

```
POD = (number of distinct days the species appears) / (number of working days)
```

— the fraction of operating days on which the species was photographed
("photographic occurrence days").

Two interval parameters control the counting (both passed to `calculate` in
**minutes**):

- `image_interval` — minimum gap between two photos for them to count as
  *separate* independent captures (typical value: 30 or 60 min).
- `event_interval` — gap that separates two *events* (used for `event_count`,
  not for the OI values themselves).

The default occasion/session framing noted in the code:

> POD: occasion (回合) = 1 day, session (期間) = 1 month
> APOA: occasion = 1 hour

---

## 2. Where each input comes from in the Camtrap DP package

`Deployment.calculate` reads three things from the database. Here is the
equivalent source in the exported package:

| `calculate` needs | From the live DB | From the Camtrap DP package |
|-------------------|------------------|------------------------------|
| The species photos (datetime, individual id) | `Image` rows for the deployment / species, `is_duplicated != 'Y'` | `observations.csv` rows filtered by `scientificName` (duplicates already excluded at export) |
| The capture timestamp | `Image.datetime` (stored UTC, shifted +08:00 in code) | `observations.csv.timestamp` — **already `+08:00`**, no shift needed |
| The individual id | `Image.animal_id` | `observations.csv.individualID` |
| Camera working time | `Deployment.count_working_day()` from `DeploymentJournal` (gaps excluded) | `deployments.csv` `deploymentStart` / `deploymentEnd` ranges |

### Key column mapping

**`observations.csv`** (one row per classified photo, `observationLevel = media`):

| Column | Meaning | `calculate` equivalent |
|--------|---------|------------------------|
| `deploymentID` | `j-<journal_id>` (or `dep-<id>` for legacy projects) | groups photos per camera session |
| `mediaID` | image uuid | `Image.image_uuid` |
| `timestamp` / `eventStart` | capture time, `+08:00` | `Image.datetime` (after TW shift) |
| `scientificName` | species name | `Image.species` |
| `individualID` | individual animal id | `Image.animal_id` |
| `observationType` | `animal` or `blank` | `'animal' if species else 'blank'` |

**`deployments.csv`** (one row per camera working session):

| Column | Meaning |
|--------|---------|
| `deploymentID` | `j-<journal_id>` — matches `observations.deploymentID` |
| `locationID` | `loc-<deployment_id>` — the physical camera point |
| `deploymentStart` / `deploymentEnd` | working window, `+08:00` (gaps already split into separate rows / excluded) |

> **Important grouping note.** In the export, one Camtrap *deployment*
> (`j-<journal_id>`) = one `DeploymentJournal` = one continuous working session.
> A single physical camera point (`locationID = loc-<deployment_id>`) may have
> **several** deployment rows. To reproduce `Deployment.calculate`, which works
> per *physical deployment*, you must **group by `locationID`**, not by
> `deploymentID`.

---

## 3. Effective camera hours (the denominator)

In `calculate`:

```python
working_days = self.count_working_day(year, month)[0]   # list of 0/1 per day
sum_working_hours = sum(working_days) * 24
```

`count_working_day` marks each calendar day `1` if any effective (non-gap)
`DeploymentJournal` covers it, then effort = (working-day count) × 24.
**Resolution is whole days, not partial hours.**

To reproduce this from `deployments.csv` for a location and a target month:

1. Take every `deployments.csv` row whose `locationID` is the camera point.
2. For each row, take the set of **calendar dates** between `deploymentStart`
   and `deploymentEnd` (inclusive) that fall inside the target month.
3. Union those date sets across all rows (so overlapping sessions aren't
   double-counted).
4. `working_days = number of distinct dates`; `effective_camera_hours =
   working_days × 24`.

```python
from datetime import date, timedelta

def working_days_in_month(dep_rows, year, month):
    days = set()
    for r in dep_rows:                       # rows for one locationID
        start = parse_iso(r['deploymentStart']).date()
        end   = parse_iso(r['deploymentEnd']).date()
        d = start
        while d <= end:
            if d.year == year and d.month == month:
                days.add(d)
            d += timedelta(days=1)
    return len(days)
```

> **Legacy projects** export `deploymentID = dep-<id>` and derive
> `deploymentStart`/`deploymentEnd` from the min/max photo datetime (see
> `write_deployments_legacy`). There the effort is only an approximation of the
> true working period — flag any index computed from legacy packages as
> approximate.

---

## 4. Independent-capture counting (the numerator)

This is the core of `Deployment.calculate`. The numerator for OI3/OI2 is the
number of photos that survive the "collapse photos closer than `image_interval`"
rule. Below is a clean reference implementation operating on `observations.csv`
rows, matching the intent of the model.

### OI3 — time-based, no individual ID

```python
def count_oi3(obs, image_interval_min):
    """obs: species rows (observationType='animal') sorted by timestamp."""
    threshold = image_interval_min * 60
    count = 0
    last = None
    delta_acc = 0          # seconds accumulated since the last *counted* photo
    for o in obs:
        t = parse_iso(o['timestamp'])
        if last is None:
            count = 1               # first photo always counts
        else:
            delta_acc += (t - last).total_seconds()
            if delta_acc >= threshold:
                count += 1
                delta_acc = 0       # reset only when a new capture is counted
        last = t
    return count
```

OI3 in the model is incremented **only for photos without an `individualID`**
(the `else` branch of the loop). If your dataset never fills `individualID`
(the common case), OI3 counts every species photo under the interval rule — this
is the value most projects use.

### OI1 — individual-aware

```python
def count_oi1(obs, image_interval_min):
    """obs sorted by timestamp; uses individualID."""
    threshold = image_interval_min * 60
    count = 0
    last = None
    delta_acc = 0
    prev_individual = None
    for o in obs:
        t = parse_iso(o['timestamp'])
        ind = (o.get('individualID') or '').strip()
        if last is None:
            count = 1 if ind else 0     # first photo counts only if it has an id
            prev_individual = ind or None
        else:
            delta_acc += (t - last).total_seconds()
            if ind:
                if prev_individual is not None:
                    if ind != prev_individual:      # different individual → new capture
                        count += 1
                    elif delta_acc >= threshold:    # same individual, reappeared later
                        count += 1
                        delta_acc = 0
                else:
                    prev_individual = ind
                    count += 1
        last = t
    return count
```

### OI2 — time-based, individual ignored

Conceptually OI2 is OI3 *applied to all species photos regardless of individual
ID*. (Note: the in-DB OI2 loop in `Deployment.calculate` has a known bug — it
reuses a stale `image_dt`, so its deltas are effectively zero and the count
collapses. The clean intent is simply `count_oi3` run over *all* species rows,
not just the no-id ones.)

```python
def count_oi2(obs, image_interval_min):
    return count_oi3(obs, image_interval_min)   # same rule, over all species photos
```

### Turning counts into indices

```python
def oi(count, working_days):
    hours = working_days * 24
    return (count / hours) * 1000 if hours > 0 else None   # 'N/A' in the model
```

---

## 5. POD — photographic occurrence days

```python
def count_pod(obs, working_days):
    days_with_species = {parse_iso(o['timestamp']).date() for o in obs}
    return len(days_with_species) / working_days if working_days > 0 else None
```

In the model this is `by_day.count() / sum(working_days)` — distinct days on
which the species appears, over total working days.

---

## 6. Activity pattern grid (`mdh`)

The last element of `calculate`'s result is a month×day×hour presence grid used
for activity-pattern (POA) plots:

```
mdh[day] = [day_has_species(0/1), [hour_0_has_species, ... hour_23]]
```

From `observations.csv` this is just: for each species photo, mark
`mdh[timestamp.day-1][0] = 1` and `mdh[timestamp.day-1][1][timestamp.hour] = 1`.

> The model shifts hours from UTC to Taipei (`utc_hour + 8`) because
> `Image.datetime` is stored UTC. **In the Camtrap DP export the `timestamp` is
> already `+08:00`, so no hour shift is required** — use `timestamp.hour`
> directly.

---

## 7. End-to-end recipe (one species, one location, one month)

```python
import csv
from datetime import datetime

def parse_iso(s):
    return datetime.fromisoformat(s)   # export uses ISO-8601 with +08:00

def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

deployments  = load('deployments.csv')
observations = load('observations.csv')

location_id   = 'loc-12345'
species       = '山羌'
year, month   = 2024, 3
image_interval = 30        # minutes
event_interval = 60        # minutes (only for event_count)

# 1. deployment rows for this physical camera point
dep_rows = [d for d in deployments if d['locationID'] == location_id]
dep_ids  = {d['deploymentID'] for d in dep_rows}

# 2. effective camera hours
wdays = working_days_in_month(dep_rows, year, month)

# 3. species photos at this location, in the target month, sorted by time
obs = [
    o for o in observations
    if o['deploymentID'] in dep_ids
    and o['observationType'] == 'animal'
    and o['scientificName'] == species
    and parse_iso(o['timestamp']).year == year
    and parse_iso(o['timestamp']).month == month
]
obs.sort(key=lambda o: o['timestamp'])

# 4. indices
oi1 = oi(count_oi1(obs, image_interval), wdays)
oi2 = oi(count_oi2(obs, image_interval), wdays)
oi3 = oi(count_oi3(obs, image_interval), wdays)
pod = count_pod(obs, wdays)

print(year, month, species, 'OI1', oi1, 'OI2', oi2, 'OI3', oi3, 'POD', pod)
```

---

## 8. Differences vs. the live `Deployment.calculate`

Reproducing from the package will be *close to but not bit-identical* with the
in-DB result. Known reasons:

1. **Effort resolution.** Both compute effort as `working_days × 24`. As long as
   gaps were exported correctly (they are filtered out at export via
   `is_gap`), the working-day set should match. Legacy (`dep-*`) packages derive
   the window from photo min/max and are only approximate.
2. **Month boundary / timezone.** The model selects images using a UTC range
   that corresponds to the Taipei month; the package timestamps are already
   `+08:00`, so filtering directly on `timestamp.month` is the natural
   equivalent and avoids the UTC↔TW edge handling.
3. **OI2 bug.** The live OI2 is broken (stale `image_dt`); the recipe above uses
   the intended definition (OI3 rule over all species rows).
4. **Duplicates.** `is_duplicated = 'Y'` images are excluded *at export time*, so
   the package already matches the model's `.exclude(is_duplicated='Y')`.
5. **Individual IDs.** `OI1` only diverges from `OI2`/`OI3` when
   `individualID` is populated; for most projects it is empty and the three
   numerators converge.
