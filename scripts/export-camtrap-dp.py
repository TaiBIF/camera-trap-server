"""
Export project data to Camtrap DP (Camera Trap Data Package) format.

Spec: https://camtrap-dp.tdwg.org/  (profile: 1.0)

For each exported project, writes a directory containing:
  datapackage.json     — Frictionless descriptor + Camtrap DP metadata
  deployments.csv      — one row per DeploymentJournal (camera operation session),
                         plus one per camera location for images with no journal
  media.csv            — one row per Image
  observations.csv     — one row per classified Image (observationLevel=media)

Mapping notes:
  - A Camtrap "deployment" = one DeploymentJournal record (working_start..working_end),
    because the spec defines deployment as a camera at a location for a time period.
    The Deployment.id is exported as locationID, Deployment.name as locationName.
    Images without a journal link (legacy-system imports) are exported under a
    per-location deployment (deploymentID dep-{Deployment.id}) whose period is
    the min/max of their timestamps; projects with no journals use only these.
  - Test locations (placeholder coordinates 1, 1) are not exported, nor their images.
  - Coordinates are WGS84. Deployments stored as TWD97 TM2 metres are reprojected.
  - timestampIssues=true when a deployment's own period or any of its media
    timestamps is implausible (before 2000 or after the export), or media fall
    more than 1 day outside the deployment period. Media are still exported.
  - Image.datetime is stored in UTC, shifted to +08:00 on output.
  - DeploymentJournal.working_start/end is stored as naive Taipei time, tagged +08:00.
  - Image.species is a free-text label that also encodes test/blank/human shots.
    classify_observation() maps it to Camtrap DP vocab:
      * real species          → observationType='animal'
      * 空拍/錯誤空拍          → 'blank'
      * 測試/test (timelapse)  → 'blank', captureMethod='timeLapse'
      * 工作照/收相機 (setup)  → 'human', cameraSetupType='setup'
      * Species.EXCLUDE_LIST   → NOT exported at all (real people, privacy)
  - For animal observations, the Chinese label is resolved to a real Latin
    scientificName via the TaiCOL map (species-taicol-map.csv, --species-map).
    Labels with no Latin name keep observationType='animal' with an empty
    scientificName; the original label is preserved in observationComments.
    The package-level taxonomic[] block carries each scientificName with its
    TaiCOL taxonID and the Chinese name under vernacularNames (zho).
  - cameraModel is taken from EXIF Make/Model in taicat_image_info, using one
    representative image per deployment (formatted "Make-Model").
  - Package-level spatial (GeoJSON bbox) and temporal (start/end) are derived
    from the written deployments; both are top-level (not under project), as the
    Camtrap DP profile / GBIF IPT require. --zip writes an upload-ready archive
    with the files at the root (IPT needs datapackage.json at the zip root).

Usage:
  python scripts/export-camtrap-dp.py --project-id 287
  python scripts/export-camtrap-dp.py --project-id 287,288 -o /tmp/dp
  python scripts/export-camtrap-dp.py --all-published
  python scripts/export-camtrap-dp.py --project-id 287 --zip   # for IPT upload
"""

import argparse
import csv
import json
import os
import re
import sys
import zipfile
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db.models import Max, Min, Q

from taicat.models import (
    Deployment,
    DeploymentJournal,
    Image,
    Image_info,
    Project,
    Species,
)

# --- Species-label handling for observations -------------------------------
# TaiCAT stores test/blank/human markers in Image.species rather than in a
# dedicated field. Map them to the Camtrap DP controlled vocabularies instead
# of treating every non-empty label as a real animal. See
# docs/camtrap-dp-export.md for the full rationale.

# Real people / hunters caught incidentally — NOT exported at all (privacy).
EXCLUDE_SPECIES = set(Species.EXCLUDE_LIST)

# Camera setup / pickup shots (person in frame); these mark deployment
# boundaries → observationType=human, cameraSetup=true.
SETUP_SPECIES = {'工作照', '收相機', '研究人員到點結束片'}

# Scheduled "camera is alive" test frames → captureMethod=timeLapse, blank.
TIMELAPSE_SPECIES = {'測試', '曠時攝影測試相機工作意思一下', 'test'}

# Empty triggers, no animal → blank.
BLANK_SPECIES = {'空拍', '錯誤空拍', '空拍(黑)'}

# TaiCAT species label → TaiCOL scientific name mapping (built by
# scripts/export-species-taicol.py, then hand-curated). Used to put real Latin
# names in observations.scientificName and to build the taxonomic block.
DEFAULT_SPECIES_MAP = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'species-taicol-map.csv')

# Chinese vernacular names are tagged with this ISO 639-3 language code.
VERNACULAR_LANG = 'zho'

CAMTRAP_DP_PROFILE = 'https://rs.gbif.org/data-packages/camtrap-dp/1.0/profile/camtrap-dp-profile.json'

TW_TZ = timezone(timedelta(hours=8))

LICENSE_MAP = {
    'cc0':   {'name': 'CC0-1.0',     'path': 'https://creativecommons.org/publicdomain/zero/1.0/'},
    'by':    {'name': 'CC-BY-4.0',   'path': 'https://creativecommons.org/licenses/by/4.0/'},
    'by-nc': {'name': 'CC-BY-NC-4.0','path': 'https://creativecommons.org/licenses/by-nc/4.0/'},
}

DEPLOYMENT_COLUMNS = [
    'deploymentID', 'locationID', 'locationName', 'latitude', 'longitude',
    'coordinateUncertainty', 'deploymentStart', 'deploymentEnd', 'setupBy',
    'cameraID', 'cameraModel', 'cameraDelay', 'cameraHeight', 'cameraDepth',
    'cameraTilt', 'cameraHeading', 'detectionDistance', 'timestampIssues',
    'baitUse', 'featureType', 'habitat', 'deploymentGroups', 'deploymentTags',
    'deploymentComments',
]

MEDIA_COLUMNS = [
    'mediaID', 'deploymentID', 'captureMethod', 'timestamp', 'filePath',
    'filePublic', 'fileName', 'fileMediatype', 'exifData', 'favorite',
    'mediaComments',
]

# Field names and order follow the Camtrap DP 1.0 observations table schema:
# https://rs.gbif.org/data-packages/camtrap-dp/1.0/table-schemas/observations.json
# (there is no 'taxonID'; the setup flag is 'cameraSetupType', enum setup/calibration)
OBSERVATION_COLUMNS = [
    'observationID', 'deploymentID', 'mediaID', 'eventID', 'eventStart',
    'eventEnd', 'observationLevel', 'observationType', 'cameraSetupType',
    'scientificName', 'count', 'lifeStage', 'sex', 'behavior',
    'individualID', 'classificationMethod', 'classifiedBy',
    'classificationTimestamp', 'classificationProbability',
    'observationTags', 'observationComments',
]


def safe_slug(value):
    keep = [c if c.isalnum() or c in ('-', '_') else '-' for c in (value or '')]
    slug = ''.join(keep).strip('-')
    return slug or 'project'


def license_entry(code, scope):
    if not code:
        return None
    entry = LICENSE_MAP.get(code.lower())
    if not entry:
        return {'name': code, 'scope': scope}
    return {**entry, 'scope': scope}


def as_tw(dt, assume_naive_tw=False):
    """Return dt as an aware +08:00 datetime, or None.

    assume_naive_tw=True  → input is naive Taipei time (DeploymentJournal)
    assume_naive_tw=False → input is UTC (Image.datetime), convert to +08:00
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TW_TZ if assume_naive_tw else timezone.utc)
    return dt.astimezone(TW_TZ)


def to_iso_tw(dt, assume_naive_tw=False):
    """Format datetime as ISO 8601 with +08:00. Returns '' for None."""
    dt = as_tw(dt, assume_naive_tw)
    return dt.isoformat(timespec='seconds') if dt else ''


# Timestamps before PLAUSIBLE_START or after the export time cannot be real
# captures (camera clocks reset to 1980, set years ahead, typos like 0321).
# Such images are still exported, but their deployment gets timestampIssues=true,
# as does a deployment with media more than TIMESTAMP_TOLERANCE outside its
# deploymentStart..deploymentEnd.
PLAUSIBLE_START = datetime(2000, 1, 1, tzinfo=TW_TZ)
EXPORT_TIME = datetime.now(TW_TZ).replace(microsecond=0)
TIMESTAMP_TOLERANCE = timedelta(days=1)


def timestamp_plausible(dt):
    return PLAUSIBLE_START <= dt <= EXPORT_TIME


def is_placeholder_location(dep):
    """True for test / dummy camera locations. These are entered with the
    placeholder coordinates (1, 1) — e.g. project 329's test, test0621 — and
    their images must not be published."""
    return dep.latitude == 1 and dep.longitude == 1


def wgs84_coordinates(dep):
    """Return (latitude, longitude) in WGS84 degrees for a Deployment, '' if unset.

    Deployments marked TWD97 usually store TM2 zone 121 metres (EPSG:3826) in
    longitude/latitude, which Camtrap DP cannot take; those are reprojected to
    EPSG:4326. Values already in degrees are kept as they are — the same rule
    taicat.utils.find_named_area uses.
    """
    if dep.latitude is None or dep.longitude is None:
        return '', ''
    x, y = float(dep.longitude), float(dep.latitude)
    in_degrees = 114.32 <= x <= 123.61 and 17.36 <= y <= 26.96
    if dep.geodetic_datum != 'TWD97' or in_degrees:
        return dep.latitude, dep.longitude
    pnt = Point(x=x, y=y, srid=3826)
    pnt.transform(4326)
    return f'{pnt.y:.8f}', f'{pnt.x:.8f}'


def load_species_map(path):
    """Load the TaiCAT-label → TaiCOL mapping CSV.

    Returns dict: label -> {'sci': scientific_name, 'taxon_id': taicol_taxon_id}.
    Curated rows that have a taxon_id but an empty scientific_name are backfilled
    from any other row sharing that taxon_id (so e.g. 獼猴 → t0068195 inherits
    'Macaca cyclopis' from 臺灣獼猴). Labels are keyed verbatim (some carry
    significant leading/trailing spaces); lookup also falls back to stripped.
    """
    if not path or not os.path.exists(path):
        if path:
            print(f'  ! species map not found: {path} (scientificName left blank)',
                  file=sys.stderr)
        return {}
    rows = []
    with open(path, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    id2sci = {r['taicol_taxon_id']: r['scientific_name']
              for r in rows if r.get('taicol_taxon_id') and r.get('scientific_name')}
    mapping = {}
    for r in rows:
        name = r.get('name')
        if name is None:
            continue
        taxon_id = (r.get('taicol_taxon_id') or '').strip()
        sci = (r.get('scientific_name') or '').strip()
        if not sci and taxon_id:
            sci = id2sci.get(taxon_id, '')
        # the CSV has duplicate labels (e.g. 獼猴 appears curated AND as a plain
        # no-match row); never let an empty duplicate clobber a populated one
        existing = mapping.get(name)
        if existing and (existing['sci'] or existing['taxon_id']) and not (sci or taxon_id):
            continue
        mapping[name] = {'sci': sci, 'taxon_id': taxon_id}
    return mapping


def resolve_species(species_map, raw):
    """Look up a raw Image.species label, falling back to its stripped form."""
    if raw in species_map:
        return species_map[raw]
    return species_map.get((raw or '').strip())


def classify_observation(species):
    """Map a TaiCAT Image.species label to Camtrap DP observation fields.

    Returns a dict with observationType / scientificName / count /
    cameraSetupType / captureMethod, or None when the image must NOT be exported
    (real people in EXCLUDE_SPECIES — dropped for privacy, media + observation).

    observationType / cameraSetupType use the Camtrap DP 1.0 controlled
    vocabularies (cameraSetupType enum: setup, calibration; '' = not a setup).
    """
    s = (species or '').strip()
    if s in EXCLUDE_SPECIES:
        return None
    if not s or s in BLANK_SPECIES:
        return {'observationType': 'blank', 'scientificName': '', 'count': '',
                'cameraSetupType': '', 'captureMethod': 'activityDetection'}
    if s in SETUP_SPECIES:
        return {'observationType': 'human', 'scientificName': '', 'count': '',
                'cameraSetupType': 'setup', 'captureMethod': 'activityDetection'}
    if s in TIMELAPSE_SPECIES:
        # scheduled "alive" test frames: marked via captureMethod=timeLapse only.
        # cameraSetupType is left empty — 'calibration' means a calibration
        # action (not an alive-check) and would just duplicate captureMethod.
        return {'observationType': 'blank', 'scientificName': '', 'count': '',
                'cameraSetupType': '', 'captureMethod': 'timeLapse'}
    return {'observationType': 'animal', 'scientificName': s, 'count': 1,
            'cameraSetupType': '', 'captureMethod': 'activityDetection'}


def extract_camera_model(exif):
    """Return a Camtrap 'manufacturer-model' string from an Image_info.exif value.

    Two storage formats exist in taicat_image_info.exif:
      dict — EXIF tags from newer uploads, keys 'Make'/'Model'
      str  — legacy Mongo doc repr containing "'make': '...'" / "'model': '...'"
    Returns '' when no camera info is available.
    """
    make = model = ''
    if isinstance(exif, dict):
        make = str(exif.get('Make') or '').strip()
        model = str(exif.get('Model') or '').strip()
    elif isinstance(exif, str):
        if m := re.search(r"'make': '([^']*)'", exif):
            make = m.group(1).strip()
        if m := re.search(r"'model': '([^']*)'", exif):
            model = m.group(1).strip()
    if make and model:
        return f'{make}-{model}'
    return make or model


def build_camera_model_map(project, group_field):
    """Map unit id (DeploymentJournal id or Deployment id) → cameraModel string.

    Per unit, up to two candidate images (min/max image_uuid) are collected and
    their EXIF fetched from taicat_image_info. That table has no index on
    image_uuid, so all candidates go into a single IN query — one sequential
    scan per project instead of one per deployment.
    """
    candidates = (
        Image.objects
        .filter(project_id=project.id)
        .exclude(is_duplicated='Y')
        .exclude(image_uuid__isnull=True)
        .exclude(image_uuid='')
        .values(group_field)
        .annotate(u1=Min('image_uuid'), u2=Max('image_uuid'))
    )
    uuid_to_unit = {}
    for row in candidates:
        unit = row[group_field]
        if unit is None:
            continue
        for u in (row['u1'], row['u2']):
            if u:
                uuid_to_unit[u] = unit

    result = {}
    if not uuid_to_unit:
        return result
    infos = (
        Image_info.objects
        .filter(image_uuid__in=list(uuid_to_unit))
        .values_list('image_uuid', 'exif')
    )
    for uuid, exif in infos.iterator(chunk_size=500):
        unit = uuid_to_unit[uuid]
        if result.get(unit):
            continue
        if camera_model := extract_camera_model(exif):
            result[unit] = camera_model
    return result


# Camtrap DP deployments-table required fields (besides deploymentID, which is
# always set). A row missing any of these is invalid, so it is skipped — and its
# media/observations are never fetched.
REQUIRED_DEPLOYMENT_FIELDS = ('latitude', 'longitude', 'deploymentStart', 'deploymentEnd')


def deployment_row_valid(row):
    return all(row[f] != '' for f in REQUIRED_DEPLOYMENT_FIELDS)


# One Camtrap deployment to export: its deployments.csv row, the Image filter
# selecting its media, and its period as aware +08:00 datetimes.
Unit = namedtuple('Unit', 'row image_filter start end')


class GeoTemporal:
    """Accumulates deployment coordinates and working dates to derive the
    package-level `spatial` (GeoJSON) and `temporal` (start/end) metadata, which
    Camtrap DP / IPT require at the top level."""

    def __init__(self):
        self.lons, self.lats, self.starts, self.ends = [], [], [], []

    def add(self, row, start, end):
        try:
            self.lons.append(float(row['longitude']))
            self.lats.append(float(row['latitude']))
        except (TypeError, ValueError):
            pass
        # implausible dates (clock resets etc.) would stretch the package period
        if timestamp_plausible(start):
            self.starts.append(row['deploymentStart'])
        if timestamp_plausible(end):
            self.ends.append(row['deploymentEnd'])

    def spatial(self):
        if not self.lons:
            return None
        min_lon, max_lon = min(self.lons), max(self.lons)
        min_lat, max_lat = min(self.lats), max(self.lats)
        if min_lon == max_lon and min_lat == max_lat:
            return {'type': 'Point', 'coordinates': [min_lon, min_lat]}
        return {
            'type': 'Polygon',
            'bbox': [min_lon, min_lat, max_lon, max_lat],
            'coordinates': [[
                [min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat],
                [min_lon, max_lat], [min_lon, min_lat],
            ]],
        }

    def temporal(self):
        if not self.starts and not self.ends:
            return None
        return {
            'start': (min(self.starts)[:10] if self.starts else min(self.ends)[:10]),
            'end': (max(self.ends)[:10] if self.ends else max(self.starts)[:10]),
        }


def deployment_row(deployment_id, dep, start, end, camera_model, groups, comments):
    lat, lon = wgs84_coordinates(dep)
    period_ok = start is not None and end is not None and \
        timestamp_plausible(start) and timestamp_plausible(end)
    return {
        'deploymentID': deployment_id,
        'locationID': f'loc-{dep.id}',
        'locationName': dep.name,
        'latitude': lat,
        'longitude': lon,
        'coordinateUncertainty': '',
        'deploymentStart': start.isoformat(timespec='seconds') if start else '',
        'deploymentEnd': end.isoformat(timespec='seconds') if end else '',
        'setupBy': '',
        'cameraID': '',
        'cameraModel': camera_model,
        'cameraDelay': '',
        'cameraHeight': dep.altitude if dep.altitude is not None else '',
        'cameraDepth': '',
        'cameraTilt': '',
        'cameraHeading': '',
        'detectionDistance': '',
        'timestampIssues': 'false' if period_ok else 'true',
        'baitUse': '',
        'featureType': '',
        'habitat': dep.vegetation or dep.landcover or '',
        'deploymentGroups': groups,
        'deploymentTags': '',
        'deploymentComments': comments,
    }


def journal_units(project, geo):
    """One Camtrap deployment per effective DeploymentJournal (a camera at a
    location for one working period, working_start..working_end)."""
    # is_gap may be NULL (legacy) or False; both mean "not a gap" — match the
    # idiom used by Deployment.count_working_day (taicat/models.py).
    journals = (
        DeploymentJournal.objects
        .filter(project_id=project.id, is_effective=True)
        .filter(Q(is_gap__isnull=True) | Q(is_gap=False))
        .select_related('deployment', 'studyarea')
        .order_by('deployment_id', 'working_start')
    )

    camera_models = build_camera_model_map(project, 'deployment_journal_id')

    units = []
    for j in journals.iterator(chunk_size=500):
        dep = j.deployment
        if dep is None or dep.deprecated or is_placeholder_location(dep):
            continue
        start = as_tw(j.working_start, assume_naive_tw=True)
        end = as_tw(j.working_end, assume_naive_tw=True)
        row = deployment_row(
            f'j-{j.id}', dep, start, end, camera_models.get(j.id, ''),
            j.studyarea.name if j.studyarea_id else '', j.folder_name or '')
        if not deployment_row_valid(row):
            # missing a required field (e.g. null working_start/end); skip
            continue
        geo.add(row, start, end)
        units.append(Unit(row, {'deployment_journal_id': j.id}, start, end))
    return units


def location_units(project, geo, unlinked_only):
    """One Camtrap deployment per Deployment (camera location), for images that
    are not linked to a DeploymentJournal.

    Used for old projects with no journals at all, and — with unlinked_only=True —
    for images in journal projects that carry no deployment_journal_id (imports
    from the legacy system, older uploads). The working period is the min/max
    plausible Image.datetime at that location; implausible datetimes are only
    used when a location has nothing else.
    """
    images = Image.objects.filter(project_id=project.id).exclude(is_duplicated='Y')
    if unlinked_only:
        images = images.filter(deployment_journal_id__isnull=True)
    plausible = Q(datetime__gte=PLAUSIBLE_START, datetime__lte=EXPORT_TIME)
    ranges = {
        r['deployment_id']: (r['ok_min'] or r['dt_min'], r['ok_max'] or r['dt_max'])
        for r in (
            images
            .values('deployment_id')
            .annotate(dt_min=Min('datetime'), dt_max=Max('datetime'),
                      ok_min=Min('datetime', filter=plausible),
                      ok_max=Max('datetime', filter=plausible))
        )
        if r['deployment_id'] is not None
    }
    if not ranges:
        return []

    deployments = (
        Deployment.objects
        .filter(project_id=project.id, deprecated=False, id__in=list(ranges))
        .select_related('study_area')
        .order_by('id')
    )

    camera_models = build_camera_model_map(project, 'deployment_id')

    image_filter = {'deployment_journal_id__isnull': True} if unlinked_only else {}
    units = []
    for dep in deployments.iterator(chunk_size=500):
        if is_placeholder_location(dep):
            continue
        dt_min, dt_max = ranges[dep.id]
        start, end = as_tw(dt_min), as_tw(dt_max)
        row = deployment_row(
            f'dep-{dep.id}', dep, start, end, camera_models.get(dep.id, ''),
            dep.study_area.name if dep.study_area_id else '', '')
        if not deployment_row_valid(row):
            continue
        geo.add(row, start, end)
        units.append(Unit(row, {'deployment_id': dep.id, **image_filter}, start, end))
    return units


def write_deployments(out_dir, units, timestamp_issues):
    """Write deployments.csv; timestamp_issues holds the deploymentIDs whose media
    fell outside their period (found while writing media)."""
    with (out_dir / 'deployments.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=DEPLOYMENT_COLUMNS)
        writer.writeheader()
        for unit in units:
            row = unit.row
            if row['deploymentID'] in timestamp_issues:
                row = {**row, 'timestampIssues': 'true'}
            writer.writerow(row)


# Only the Image columns the writer reads, fetched as plain tuples (in this
# order) rather than model instances — building a Django object per row was a
# large share of the runtime on multi-million-image projects. Skipping the JSON
# columns (annotation, source_data, remarks2) also avoids detoasting them.
IMAGE_EXPORT_FIELDS = (
    'id', 'species', 'datetime', 'image_uuid', 'remarks', 'from_mongo',
    'file_url', 'specific_bucket', 'filename', 'folder_name', 'life_stage',
    'sex', 'animal_id', 'antler',
)


def write_media_and_observations(project, units, out_dir, species_map):
    """Fetch images unit by unit and write both media.csv and observations.csv.

    Images are queried one Unit (deployment) at a time via its image_filter,
    which hits the deployment_journal_id / deployment_id index, instead of one
    project-wide `ORDER BY id` query: outside a
    transaction Django opens its server-side cursor WITH HOLD, so PostgreSQL
    materializes the whole result before returning a row — for a large project
    (e.g. 329, ~21M images) that is many GB of sort + temp files and can take
    the server down. Images whose unit was not written are never fetched.

    For animal observations, the Chinese label is resolved to a Latin
    scientificName via species_map. Labels with no Latin name keep
    observationType=animal but with an empty scientificName, and the original
    label is preserved in observationComments so the identification is not lost.

    Returns (n_media, n_obs, taxa, timestamp_issues) where taxa maps
    scientificName -> {'taxonID', 'vernacular'} for every taxon actually written
    (used to build the package-level taxonomic block), and timestamp_issues is
    the set of deploymentIDs with media timestamps that are implausible or more
    than TIMESTAMP_TOLERANCE outside the deployment period.
    """
    media_path = out_dir / 'media.csv'
    obs_path = out_dir / 'observations.csv'
    file_public = 'true' if project.is_public else 'false'
    default_bucket = getattr(settings, 'AWS_S3_BUCKET', '')

    # There are only a few hundred distinct labels, so classify and resolve
    # each one once instead of once per image.
    label_cache = {}

    def classify_label(species):
        if species not in label_cache:
            obs = classify_observation(species)
            info = None
            if obs is not None and obs['observationType'] == 'animal':
                info = resolve_species(species_map, species or '')
            label_cache[species] = (obs, info)
        return label_cache[species]

    n_media = 0
    n_obs = 0
    taxa = {}
    timestamp_issues = set()
    with media_path.open('w', newline='', encoding='utf-8') as mf, \
         obs_path.open('w', newline='', encoding='utf-8') as of:
        media_writer = csv.writer(mf)
        obs_writer = csv.writer(of)
        media_writer.writerow(MEDIA_COLUMNS)
        obs_writer.writerow(OBSERVATION_COLUMNS)

        for i, unit in enumerate(units, 1):
            if i % 500 == 0:
                print(f'  ... {i}/{len(units)} units, {n_media} media', flush=True)
            deployment_ref = unit.row['deploymentID']
            # Media timestamps are ISO strings in the same +08:00 format, so the
            # allowed window compares as strings. Clamping before applying the
            # tolerance keeps year-1 / far-future datetimes from overflowing.
            ts_min = (max(unit.start, PLAUSIBLE_START + TIMESTAMP_TOLERANCE)
                      - TIMESTAMP_TOLERANCE).isoformat(timespec='seconds')
            ts_max = (min(unit.end, EXPORT_TIME - TIMESTAMP_TOLERANCE)
                      + TIMESTAMP_TOLERANCE).isoformat(timespec='seconds')
            rows = (
                Image.objects
                .filter(project_id=project.id, **unit.image_filter)
                .exclude(is_duplicated='Y')
                .order_by('id')
                .values_list(*IMAGE_EXPORT_FIELDS)
            )
            # An image with several annotations (e.g. two species in one frame)
            # is stored as several Image rows sharing image_uuid. Camtrap DP wants
            # one media row with several observations, so write each mediaID once.
            # Shared image_uuids never span deployments, so a per-unit set suffices.
            media_written = set()
            for (img_id, species, dt, image_uuid, remarks, from_mongo, file_url,
                 specific_bucket, filename, folder_name, life_stage, sex,
                 animal_id, antler) in rows.iterator(chunk_size=2000):
                obs, info = classify_label(species)
                if obs is None:
                    # EXCLUDE_SPECIES (real people/hunters): not exported (privacy)
                    continue
                ts = to_iso_tw(dt, assume_naive_tw=False)
                if not ts:
                    # null datetime → empty required timestamp / eventStart / eventEnd
                    continue
                if not ts_min <= ts <= ts_max:
                    timestamp_issues.add(deployment_ref)
                media_id = image_uuid or f'img-{img_id}'

                # Resolve scientificName for animal observations via the TaiCOL map.
                label = (species or '').strip()
                comments = remarks or ''
                scientific = (info or {}).get('sci') or ''
                if scientific:
                    taxa.setdefault(scientific, {
                        'taxonID': (info or {}).get('taxon_id') or '',
                        'vernacular': label,
                    })
                # Keep the original Chinese label verbatim in observationComments
                # whenever it is not already carried by scientificName — i.e. the
                # test/blank/setup shots (測試/空拍/工作照…) and animals with no
                # TaiCOL match. Mapped animals keep it as the taxonomic vernacular.
                if not scientific and label:
                    comments = f'{label} {comments}'.strip()

                # same URL logic as Image.get_associated_media
                if from_mongo:
                    file_path = f'https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/{file_url}'
                else:
                    file_path = (f'https://{specific_bucket or default_bucket}'
                                 f'.s3.ap-northeast-1.amazonaws.com/{image_uuid}-m.jpg')

                if media_id not in media_written:
                    media_written.add(media_id)
                    # column order: MEDIA_COLUMNS
                    media_writer.writerow((
                        media_id, deployment_ref, obs['captureMethod'], ts, file_path,
                        file_public, filename or '', 'image/jpeg', '', '',
                        folder_name or '',
                    ))
                    n_media += 1

                # column order: OBSERVATION_COLUMNS
                obs_writer.writerow((
                    f'obs-{img_id}', deployment_ref, media_id, media_id, ts, ts,
                    'media', obs['observationType'], obs['cameraSetupType'],
                    scientific, obs['count'], life_stage or '', sex or '', '',
                    animal_id or '', 'human', '', '', '', antler or '', comments,
                ))
                n_obs += 1
    return n_media, n_obs, taxa, timestamp_issues


def build_taxonomic(taxa):
    """Build the package-level taxonomic[] from the taxa actually written.

    taxa: scientificName -> {'taxonID', 'vernacular'}. One entry per unique
    scientificName, with TaiCOL taxonID and the Chinese vernacular name.
    """
    taxonomic = []
    for sci in sorted(taxa):
        info = taxa[sci]
        entry = {'scientificName': sci, 'kingdom': 'Animalia'}
        if info.get('taxonID'):
            entry['taxonID'] = info['taxonID']
        if info.get('vernacular'):
            entry['vernacularNames'] = {VERNACULAR_LANG: info['vernacular']}
        taxonomic.append(entry)
    return taxonomic


def build_datapackage(project, n_deployments, n_media, n_obs, taxa, geo):
    licenses = []
    for code, scope in [
        (project.interpretive_data_license, 'data'),
        (project.video_material_license, 'media'),
    ]:
        entry = license_entry(code, scope)
        if entry:
            licenses.append(entry)
    if not licenses:
        licenses = [{'name': 'CC-BY-4.0',
                     'path': 'https://creativecommons.org/licenses/by/4.0/',
                     'scope': 'data'}]

    contributors = []
    if project.principal_investigator:
        contributors.append({
            'title': project.principal_investigator,
            'role': 'principalInvestigator',
        })
    if project.executive_unit:
        contributors.append({
            'title': project.executive_unit,
            'role': 'rightsHolder',
            'organization': project.executive_unit,
        })
    if not contributors:
        # Camtrap DP / IPT expect at least one contributor
        contributors.append({'title': 'TaiCAT', 'role': 'rightsHolder',
                             'organization': 'TaiBIF'})

    # spatial + temporal are required top-level metadata (not under project).
    # Prefer the actual deployment extent; fall back to the project's dates.
    spatial = geo.spatial()
    temporal = geo.temporal()
    if not temporal:
        t = {}
        if project.start_date:
            t['start'] = project.start_date.isoformat()
        if project.end_date:
            t['end'] = project.end_date.isoformat()
        temporal = t or None

    return {
        'profile': CAMTRAP_DP_PROFILE,
        'name': f'camtrap-dp-project-{project.id}',
        'id': f'taicat-project-{project.id}',
        'title': project.name,
        'description': project.description or '',
        'created': datetime.now(TW_TZ).isoformat(timespec='seconds'),
        'keywords': [k for k in (project.keyword or '').split(',') if k.strip()],
        'contributors': contributors,
        'licenses': licenses,
        'project': {
            'id': str(project.id),
            'title': project.name,
            'acronym': project.short_title or '',
            'description': project.description or '',
            'samplingDesign': 'opportunistic',
            'captureMethod': ['activityDetection', 'timeLapse'],
            'individualAnimals': False,
            'observationLevel': ['media'],
        },
        'sources': [{
            'title': 'Taiwan Camera Trap Image Archive (TaiCAT)',
            'path': 'https://camera-trap.tw/',
        }],
        'resources': [
            {
                'name': 'deployments',
                'path': 'deployments.csv',
                'profile': 'tabular-data-resource',
                'format': 'csv',
                'mediatype': 'text/csv',
                'encoding': 'utf-8',
                'schema': 'https://rs.gbif.org/data-packages/camtrap-dp/1.0/table-schemas/deployments.json',
            },
            {
                'name': 'media',
                'path': 'media.csv',
                'profile': 'tabular-data-resource',
                'format': 'csv',
                'mediatype': 'text/csv',
                'encoding': 'utf-8',
                'schema': 'https://rs.gbif.org/data-packages/camtrap-dp/1.0/table-schemas/media.json',
            },
            {
                'name': 'observations',
                'path': 'observations.csv',
                'profile': 'tabular-data-resource',
                'format': 'csv',
                'mediatype': 'text/csv',
                'encoding': 'utf-8',
                'schema': 'https://rs.gbif.org/data-packages/camtrap-dp/1.0/table-schemas/observations.json',
            },
        ],
        **({'spatial': spatial} if spatial else {}),
        **({'temporal': temporal} if temporal else {}),
        'taxonomic': build_taxonomic(taxa),
    }


# The 4 Camtrap DP files, in the order IPT expects to find them.
PACKAGE_FILES = ['datapackage.json', 'deployments.csv', 'media.csv', 'observations.csv']


def zip_package(out_dir):
    """Zip the package with the files at the ARCHIVE ROOT (no wrapping folder).

    IPT looks for datapackage.json at the root of the uploaded zip; a wrapping
    directory makes it fail to load the metadata. Returns the zip path.
    """
    zip_path = out_dir.with_suffix('.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in PACKAGE_FILES:
            fpath = out_dir / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)   # arcname = root-level name
    return zip_path


def export_project(project, base_dir, species_map, make_zip=False):
    slug = safe_slug(project.short_title or project.name)
    out_dir = base_dir / f'project-{project.id}-{slug}'
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'[{project.id}] {project.name} → {out_dir}')

    has_journals = (
        DeploymentJournal.objects
        .filter(project_id=project.id, is_effective=True)
        .filter(Q(is_gap__isnull=True) | Q(is_gap=False))
        .exists()
    )

    geo = GeoTemporal()
    if has_journals:
        units = journal_units(project, geo)
        # Images with no journal link (legacy-system imports, older uploads)
        # would otherwise be dropped; export them per camera location instead.
        location = location_units(project, geo, unlinked_only=True)
        print(f'  deployments: {len(units)} journal + {len(location)} location-based')
        units += location
    else:
        # old project: no journal linking — build straight from taicat_deployment
        print('  (no DeploymentJournal records; using deployment-based export)')
        units = location_units(project, geo, unlinked_only=False)
        print(f'  deployments: {len(units)}')

    n_media, n_obs, taxa, timestamp_issues = write_media_and_observations(
        project, units, out_dir, species_map)
    write_deployments(out_dir, units, timestamp_issues)
    n_issues = sum(1 for u in units
                   if u.row['timestampIssues'] == 'true' or u.row['deploymentID'] in timestamp_issues)
    print(f'  media:       {n_media}')
    print(f'  observations:{n_obs}')
    print(f'  taxa:        {len(taxa)}')
    print(f'  timestampIssues: {n_issues} deployments')

    descriptor = build_datapackage(project, len(units), n_media, n_obs, taxa, geo)
    with (out_dir / 'datapackage.json').open('w', encoding='utf-8') as fh:
        json.dump(descriptor, fh, ensure_ascii=False, indent=2)

    if make_zip:
        zip_path = zip_package(out_dir)
        print(f'  zip:         {zip_path}')


def resolve_projects(args):
    if args.project_id:
        ids = [int(x) for x in args.project_id.split(',') if x.strip()]
        return list(Project.objects.filter(id__in=ids).order_by('id'))
    if args.all_published:
        return list(Project.published_objects.order_by('id'))
    raise SystemExit('error: must pass --project-id or --all-published')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project-id', help='Project id(s), comma-separated')
    parser.add_argument('--all-published', action='store_true',
                        help='Export every published project')
    parser.add_argument('-o', '--output-dir', default='camtrap-dp-export',
                        help='Output base directory (default: camtrap-dp-export)')
    parser.add_argument('--species-map', default=DEFAULT_SPECIES_MAP,
                        help='TaiCAT-label → TaiCOL scientific-name CSV '
                             f'(default: {DEFAULT_SPECIES_MAP})')
    parser.add_argument('--zip', action='store_true',
                        help='Also write a {project}.zip with files at the '
                             'archive root, ready to upload to IPT')
    args = parser.parse_args()

    base = Path(args.output_dir)
    base.mkdir(parents=True, exist_ok=True)

    species_map = load_species_map(args.species_map)
    print(f'species map: {len(species_map)} labels loaded')

    projects = resolve_projects(args)
    if not projects:
        print('No projects matched.')
        return
    for p in projects:
        export_project(p, base, species_map, make_zip=args.zip)


if __name__ == '__main__':
    main()
