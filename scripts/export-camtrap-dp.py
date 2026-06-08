"""
Export project data to Camtrap DP (Camera Trap Data Package) format.

Spec: https://camtrap-dp.tdwg.org/  (profile: 1.0)

For each exported project, writes a directory containing:
  datapackage.json     — Frictionless descriptor + Camtrap DP metadata
  deployments.csv      — one row per DeploymentJournal (camera operation session)
  media.csv            — one row per Image
  observations.csv     — one row per classified Image (observationLevel=media)

Mapping notes:
  - A Camtrap "deployment" = one DeploymentJournal record (working_start..working_end),
    because the spec defines deployment as a camera at a location for a time period.
    The Deployment.id is exported as locationID, Deployment.name as locationName.
  - Image.datetime is stored in UTC, shifted to +08:00 on output.
  - DeploymentJournal.working_start/end is stored as naive Taipei time, tagged +08:00.
  - Empty species → observationType='blank'; otherwise 'animal' with the original
    species name in scientificName (no Latin-name lookup performed).

Usage:
  python scripts/export-camtrap-dp.py --project-id 287
  python scripts/export-camtrap-dp.py --project-id 287,288 -o /tmp/dp
  python scripts/export-camtrap-dp.py --all-published
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.conf import settings
from django.db.models import Max, Min, Q

from taicat.models import (
    Deployment,
    DeploymentJournal,
    Image,
    Project,
)

CAMTRAP_DP_PROFILE = 'https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/camtrap-dp-profile.json'

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

OBSERVATION_COLUMNS = [
    'observationID', 'deploymentID', 'mediaID', 'eventID', 'eventStart',
    'eventEnd', 'observationLevel', 'observationType', 'cameraSetup',
    'taxonID', 'scientificName', 'count', 'lifeStage', 'sex', 'behavior',
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


def to_iso_tw(dt, assume_naive_tw=False):
    """Format datetime as ISO 8601 with +08:00. Returns '' for None.

    assume_naive_tw=True  → input is naive Taipei time (DeploymentJournal)
    assume_naive_tw=False → input is UTC (Image.datetime), convert to +08:00
    """
    if dt is None:
        return ''
    if assume_naive_tw:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TW_TZ)
        else:
            dt = dt.astimezone(TW_TZ)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(TW_TZ)
    return dt.isoformat(timespec='seconds')


def media_url(image):
    """Build the public media URL using the same logic as Image.get_associated_media."""
    if image.from_mongo:
        return f'https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/{image.file_url}'
    bucket = image.specific_bucket or getattr(settings, 'AWS_S3_BUCKET', '')
    return f'https://{bucket}.s3.ap-northeast-1.amazonaws.com/{image.image_uuid}-m.jpg'


def write_deployments(project, out_dir):
    """Write deployments.csv. One row per effective DeploymentJournal.

    Returns set of journal ids that were written (used to filter media/obs).
    """
    # is_gap may be NULL (legacy) or False; both mean "not a gap" — match the
    # idiom used by Deployment.count_working_day (taicat/models.py).
    journals = (
        DeploymentJournal.objects
        .filter(project_id=project.id, is_effective=True)
        .filter(Q(is_gap__isnull=True) | Q(is_gap=False))
        .select_related('deployment', 'studyarea')
        .order_by('deployment_id', 'working_start')
    )

    written_ids = set()
    path = out_dir / 'deployments.csv'
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=DEPLOYMENT_COLUMNS)
        writer.writeheader()
        for j in journals.iterator(chunk_size=500):
            dep = j.deployment
            if dep is None or dep.deprecated:
                continue
            location_name = dep.name
            if j.studyarea_id and dep.study_area_id != j.studyarea_id:
                # journal recorded under a different study area; keep deployment name only
                pass
            row = {
                'deploymentID': f'j-{j.id}',
                'locationID': f'loc-{dep.id}',
                'locationName': location_name,
                'latitude': dep.latitude if dep.latitude is not None else '',
                'longitude': dep.longitude if dep.longitude is not None else '',
                'coordinateUncertainty': '',
                'deploymentStart': to_iso_tw(j.working_start, assume_naive_tw=True),
                'deploymentEnd': to_iso_tw(j.working_end, assume_naive_tw=True),
                'setupBy': '',
                'cameraID': '',
                'cameraModel': '',
                'cameraDelay': '',
                'cameraHeight': dep.altitude if dep.altitude is not None else '',
                'cameraDepth': '',
                'cameraTilt': '',
                'cameraHeading': '',
                'detectionDistance': '',
                'timestampIssues': 'false',
                'baitUse': '',
                'featureType': '',
                'habitat': dep.vegetation or dep.landcover or '',
                'deploymentGroups': j.studyarea.name if j.studyarea_id else '',
                'deploymentTags': '',
                'deploymentComments': j.folder_name or '',
            }
            writer.writerow(row)
            written_ids.add(j.id)
    return written_ids


def write_deployments_legacy(project, out_dir):
    """Write deployments.csv for old projects that have no DeploymentJournal rows.

    One Camtrap deployment per Deployment record; the working period is derived
    from the min/max Image.datetime observed at that deployment (UTC → +08:00).

    Returns the set of deployment ids that were written (used to filter media/obs).
    """
    # min/max image datetime per deployment (UTC, like all Image.datetime values)
    ranges = {
        r['deployment_id']: (r['dt_min'], r['dt_max'])
        for r in (
            Image.objects
            .filter(project_id=project.id)
            .exclude(is_duplicated='Y')
            .values('deployment_id')
            .annotate(dt_min=Min('datetime'), dt_max=Max('datetime'))
        )
        if r['deployment_id'] is not None
    }

    deployments = (
        Deployment.objects
        .filter(project_id=project.id, deprecated=False)
        .select_related('study_area')
        .order_by('id')
    )

    written_ids = set()
    path = out_dir / 'deployments.csv'
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=DEPLOYMENT_COLUMNS)
        writer.writeheader()
        for dep in deployments.iterator(chunk_size=500):
            dt_min, dt_max = ranges.get(dep.id, (None, None))
            row = {
                'deploymentID': f'dep-{dep.id}',
                'locationID': f'loc-{dep.id}',
                'locationName': dep.name,
                'latitude': dep.latitude if dep.latitude is not None else '',
                'longitude': dep.longitude if dep.longitude is not None else '',
                'coordinateUncertainty': '',
                'deploymentStart': to_iso_tw(dt_min, assume_naive_tw=False),
                'deploymentEnd': to_iso_tw(dt_max, assume_naive_tw=False),
                'setupBy': '',
                'cameraID': '',
                'cameraModel': '',
                'cameraDelay': '',
                'cameraHeight': dep.altitude if dep.altitude is not None else '',
                'cameraDepth': '',
                'cameraTilt': '',
                'cameraHeading': '',
                'detectionDistance': '',
                'timestampIssues': 'false',
                'baitUse': '',
                'featureType': '',
                'habitat': dep.vegetation or dep.landcover or '',
                'deploymentGroups': dep.study_area.name if dep.study_area_id else '',
                'deploymentTags': '',
                'deploymentComments': '',
            }
            writer.writerow(row)
            written_ids.add(dep.id)
    return written_ids


def write_media_and_observations(project, resolve_ref, out_dir):
    """Stream images for the project and write both media.csv and observations.csv.

    resolve_ref(img) returns the deploymentID this image belongs to, or None to
    skip it. This lets the journal-based and legacy (deployment-based) exports
    share the same media/observation writer.
    """
    media_path = out_dir / 'media.csv'
    obs_path = out_dir / 'observations.csv'

    qs = (
        Image.objects
        .filter(project_id=project.id)
        .exclude(is_duplicated='Y')
        .order_by('id')
    )

    n_media = 0
    n_obs = 0
    with media_path.open('w', newline='', encoding='utf-8') as mf, \
         obs_path.open('w', newline='', encoding='utf-8') as of:
        media_writer = csv.DictWriter(mf, fieldnames=MEDIA_COLUMNS)
        obs_writer = csv.DictWriter(of, fieldnames=OBSERVATION_COLUMNS)
        media_writer.writeheader()
        obs_writer.writeheader()

        for img in qs.iterator(chunk_size=2000):
            deployment_ref = resolve_ref(img)
            if deployment_ref is None:
                continue
            media_id = img.image_uuid or f'img-{img.id}'
            ts = to_iso_tw(img.datetime, assume_naive_tw=False)

            media_writer.writerow({
                'mediaID': media_id,
                'deploymentID': deployment_ref,
                'captureMethod': 'motionDetection',
                'timestamp': ts,
                'filePath': media_url(img),
                'filePublic': 'true' if project.is_public else 'false',
                'fileName': img.filename or '',
                'fileMediatype': 'image/jpeg',
                'exifData': '',
                'favorite': '',
                'mediaComments': img.folder_name or '',
            })
            n_media += 1

            species = (img.species or '').strip()
            obs_type = 'animal' if species else 'blank'
            obs_writer.writerow({
                'observationID': f'obs-{img.id}',
                'deploymentID': deployment_ref,
                'mediaID': media_id,
                'eventID': '',
                'eventStart': ts,
                'eventEnd': ts,
                'observationLevel': 'media',
                'observationType': obs_type,
                'cameraSetup': '',
                'taxonID': '',
                'scientificName': species,
                'count': 1 if species else '',
                'lifeStage': img.life_stage or '',
                'sex': img.sex or '',
                'behavior': '',
                'individualID': img.animal_id or '',
                'classificationMethod': 'human',
                'classifiedBy': '',
                'classificationTimestamp': '',
                'classificationProbability': '',
                'observationTags': img.antler or '',
                'observationComments': img.remarks or '',
            })
            n_obs += 1
    return n_media, n_obs


def build_datapackage(project, n_deployments, n_media, n_obs):
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

    temporal = {}
    if project.start_date:
        temporal['start'] = project.start_date.isoformat()
    if project.end_date:
        temporal['end'] = project.end_date.isoformat()

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
            'captureMethod': ['motionDetection'],
            'individualAnimals': False,
            'observationLevel': ['media'],
            **({'temporal': temporal} if temporal else {}),
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
                'schema': 'https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/deployments-table-schema.json',
            },
            {
                'name': 'media',
                'path': 'media.csv',
                'profile': 'tabular-data-resource',
                'format': 'csv',
                'mediatype': 'text/csv',
                'encoding': 'utf-8',
                'schema': 'https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/media-table-schema.json',
            },
            {
                'name': 'observations',
                'path': 'observations.csv',
                'profile': 'tabular-data-resource',
                'format': 'csv',
                'mediatype': 'text/csv',
                'encoding': 'utf-8',
                'schema': 'https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/observations-table-schema.json',
            },
        ],
        '_stats': {
            'deployments': n_deployments,
            'media': n_media,
            'observations': n_obs,
        },
    }


def export_project(project, base_dir):
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

    if has_journals:
        unit_ids = write_deployments(project, out_dir)
        def resolve_ref(img):
            if img.deployment_journal_id in unit_ids:
                return f'j-{img.deployment_journal_id}'
            return None
    else:
        # old project: no journal linking — build straight from taicat_deployment
        print('  (no DeploymentJournal records; using deployment-based export)')
        unit_ids = write_deployments_legacy(project, out_dir)
        def resolve_ref(img):
            if img.deployment_id in unit_ids:
                return f'dep-{img.deployment_id}'
            return None

    print(f'  deployments: {len(unit_ids)}')

    n_media, n_obs = write_media_and_observations(project, resolve_ref, out_dir)
    print(f'  media:       {n_media}')
    print(f'  observations:{n_obs}')

    descriptor = build_datapackage(project, len(unit_ids), n_media, n_obs)
    with (out_dir / 'datapackage.json').open('w', encoding='utf-8') as fh:
        json.dump(descriptor, fh, ensure_ascii=False, indent=2)


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
    args = parser.parse_args()

    base = Path(args.output_dir)
    base.mkdir(parents=True, exist_ok=True)

    projects = resolve_projects(args)
    if not projects:
        print('No projects matched.')
        return
    for p in projects:
        export_project(p, base)


if __name__ == '__main__':
    main()
