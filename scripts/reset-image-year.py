"""
Reset the year of an upload folder's image datetimes (e.g. 2025-10-21 -> 2026-10-21).

For cameras whose clock was set to the wrong year, this shifts every image of an
upload folder onto the requested year, keeping month / day / time untouched. The
shift is computed as a whole number of years from the folder's EARLIEST image
year, so a folder that straddles a new year (Dec 2025 -> Jan 2026) keeps its
span: asking for 2026 maps 2025->2026 AND 2026->2027. The mapping is always
printed before anything is written.

Datetimes are shifted on their Taiwan-local (UTC+8) wall clock, which is what
the site displays. 2/29 in a leap year moves to 2/28 when the target year is not
a leap year; those rows are counted and reported.

The DeploymentJournal rows of the selected images (working_start / working_end)
are shifted by the same number of years, so the journal keeps matching its
images. Pass --no-journals to leave them alone.

Dry-run by default; pass --commit to write.

Usage:
  python scripts/reset-image-year.py <folder_name> <year> [options]

Options:
  --project <id>   restrict to one project (required if the folder name is
                   used by more than one project)
  --commit         perform the update inside a transaction
                   (without it, nothing is written)
  --recalc         after committing, run recalc_deployment() on every affected
                   deployment so Calculation rows follow the new dates
                   (both the vacated and the new year are reconciled)
  --no-journals    do not touch DeploymentJournal.working_start / working_end

Examples:
  python scripts/reset-image-year.py ABC0001 2026
  python scripts/reset-image-year.py ABC0001 2026 --project 329 --commit --recalc

Note: project-level aggregates (ProjectStat earliest_date / latest_date,
DeploymentStat working hours) are rebuilt by the existing stat cron scripts, not
here.
"""

import argparse
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.db import transaction
from django.utils import timezone

from taicat.models import (
    Deployment,
    DeploymentJournal,
    Image,
    timezone_tw_to_utc,
    timezone_utc_to_tw,
)
from taicat.utils import recalc_deployment

BATCH_SIZE = 2000


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('folder_name', help='upload folder name (Image.folder_name)')
    p.add_argument('year', type=int, help='target year for the folder\'s earliest images')
    p.add_argument('--project', type=int, help='project id (needed if the folder name is not unique)')
    p.add_argument('--commit', action='store_true', help='write changes (default: dry run)')
    p.add_argument('--recalc', action='store_true',
                   help='recalc Calculation rows of affected deployments after commit')
    p.add_argument('--no-journals', dest='journals', action='store_false',
                   help='leave DeploymentJournal working_start / working_end untouched')
    return p.parse_args()


def shift_year(dt, delta):
    """Shift dt by delta years on its Taiwan-local wall clock.

    Returns (new_dt, clamped) where clamped is True when a 2/29 date had to fall
    back to 2/28 because the target year is not a leap year.
    """
    local = timezone_utc_to_tw(dt)
    try:
        new_local = local.replace(year=local.year + delta)
        clamped = False
    except ValueError:  # 2/29 -> non-leap year
        new_local = local.replace(year=local.year + delta, day=28)
        clamped = True
    return timezone_tw_to_utc(new_local), clamped


def local_year(dt):
    return timezone_utc_to_tw(dt).year


def select_images(args):
    """Return the image queryset for the folder, refusing an ambiguous folder name."""
    qs = Image.objects.filter(folder_name=args.folder_name).exclude(datetime__isnull=True)
    if args.project:
        qs = qs.filter(project_id=args.project)

    if not qs.exists():
        sys.exit(f'ERROR: no images with a datetime found for folder '
                 f'"{args.folder_name}"'
                 + (f' in project {args.project}.' if args.project else '.'))

    projects = sorted(
        qs.order_by('project_id').values_list('project_id', flat=True).distinct()
    )
    if len(projects) > 1:
        sys.exit(f'ERROR: folder "{args.folder_name}" spans projects {projects}. '
                 f'Re-run with --project <id> to pick one.')
    return qs


def load_rows(qs):
    """Load (id, datetime, deployment_id) for the whole folder in one pass.

    Everything else (range, year spread, deployment list) is derived in Python:
    aggregating those in the DB means scanning the global Image.datetime index,
    which costs ~20s per query on production-sized data.
    """
    return list(qs.values_list('id', 'datetime', 'deployment_id')
                  .iterator(chunk_size=5000))


def build_updates(rows, delta):
    """Apply the shift in memory.

    Returns (objects_with_new_datetime, clamped_count, year_counts) where
    year_counts maps each source Taiwan-local year to its image count.
    """
    now = timezone.now()
    objs = []
    clamped = 0
    year_counts = {}
    for img_id, dt, _ in rows:
        y = local_year(dt)
        year_counts[y] = year_counts.get(y, 0) + 1
        new_dt, was_clamped = shift_year(dt, delta)
        objs.append(Image(id=img_id, datetime=new_dt, last_updated=now))
        clamped += was_clamped
    return objs, clamped, year_counts


def report_plan(year_counts, delta, target_year):
    """Print the per-year mapping."""
    years = sorted(year_counts)
    print(f'Target year       : {target_year} (earliest year {years[0]} -> {target_year}, '
          f'shift {delta:+d} year(s))')
    print('Year mapping (Taiwan local):')
    for y in years:
        print(f'  {y} -> {y + delta}   ({year_counts[y]} image(s))')
    if len(years) > 1:
        print('  NOTE: this folder spans several years; the whole span is shifted '
              'by the same amount so the ordering is preserved.')


def shift_journals(qs, delta, commit):
    """Shift working_start / working_end of the journals these images belong to."""
    journal_ids = sorted(
        qs.exclude(deployment_journal_id__isnull=True)
          .order_by('deployment_journal_id')
          .values_list('deployment_journal_id', flat=True)
          .distinct()
    )
    journals = list(DeploymentJournal.objects.filter(id__in=journal_ids))
    print(f'Journals to shift : {len(journals)}')

    now = timezone.now()
    to_update = []
    for dj in journals:
        outside = (Image.objects.filter(deployment_journal_id=dj.id).count()
                   - qs.filter(deployment_journal_id=dj.id).count())
        if outside:
            print(f'  WARN: journal {dj.id} has {outside} image(s) outside this folder; '
                  f'their dates are NOT shifted.')
        before = (dj.working_start, dj.working_end)
        if dj.working_start:
            dj.working_start, _ = shift_year(dj.working_start, delta)
        if dj.working_end:
            dj.working_end, _ = shift_year(dj.working_end, delta)
        dj.last_updated = now
        print(f'  journal {dj.id}: '
              f'{fmt(before[0])} / {fmt(before[1])}  ->  '
              f'{fmt(dj.working_start)} / {fmt(dj.working_end)}')
        to_update.append(dj)

    if commit and to_update:
        DeploymentJournal.objects.bulk_update(
            to_update, ['working_start', 'working_end', 'last_updated'],
            batch_size=BATCH_SIZE)
    return len(to_update)


def fmt(dt):
    return timezone_utc_to_tw(dt).strftime('%Y-%m-%d %H:%M') if dt else '-'


def main():
    args = parse_args()

    qs = select_images(args)
    project_id = qs.values_list('project_id', flat=True).first()
    rows = load_rows(qs)

    print(f'Folder            : "{args.folder_name}" (project {project_id})')
    print(f'Matched images    : {len(rows)}')

    no_datetime = Image.objects.filter(
        folder_name=args.folder_name, project_id=project_id, datetime__isnull=True).count()
    if no_datetime:
        print(f'  NOTE: {no_datetime} image(s) in this folder have no datetime and are skipped.')

    earliest = min(r[1] for r in rows)
    latest = max(r[1] for r in rows)
    print(f'Current range     : {fmt(earliest)} .. {fmt(latest)}')

    delta = args.year - local_year(earliest)
    if delta == 0:
        print(f'\nEarliest images are already in {args.year}. Nothing to do.')
        return

    deployment_ids = sorted({r[2] for r in rows if r[2] is not None})
    print(f'Deployments       : {deployment_ids}')

    objs, clamped, year_counts = build_updates(rows, delta)
    report_plan(year_counts, delta, args.year)
    if clamped:
        print(f'  NOTE: {clamped} image(s) on 2/29 moved to 2/28 '
              f'(target year is not a leap year).')

    new_min = min(o.datetime for o in objs)
    new_max = max(o.datetime for o in objs)
    print(f'New range         : {fmt(new_min)} .. {fmt(new_max)}')

    if not args.commit:
        if args.journals:
            shift_journals(qs, delta, commit=False)
        print('\nDRY RUN — no changes written. Re-run with --commit to apply.')
        return

    with transaction.atomic():
        Image.objects.bulk_update(objs, ['datetime', 'last_updated'],
                                  batch_size=BATCH_SIZE)
        n_journals = shift_journals(qs, delta, commit=True) if args.journals else 0

    print(f'\nDONE: shifted {len(objs)} image(s) by {delta:+d} year(s)'
          + (f', {n_journals} journal(s).' if args.journals else '.'))

    if args.recalc:
        touched = sorted(year_counts) + [y + delta for y in year_counts]
        print('\nRecalculating Calculation rows '
              f'(years {min(touched)}..{max(touched)})...')
        for dep_id in deployment_ids:
            dep = Deployment.objects.filter(id=dep_id).first()
            if not dep:
                continue
            cells, prune = recalc_deployment(dep)
            print(f'  deployment {dep_id}: {len(cells)} cell(s) recomputed, '
                  f'{prune[1]} orphan row(s) pruned')
    else:
        print('\nCalculation rows are now stale for the affected deployments. Run:')
        print('  python scripts/recalc-deployment.py '
              + ' '.join(f'--deployment-id {d}' for d in deployment_ids))


if __name__ == '__main__':
    main()
