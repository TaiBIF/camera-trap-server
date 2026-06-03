"""
Recalculate Calculation data affected by image edits recorded in ModifiedImage.

When a user edits an image (species / life_stage / ... ) the change is logged in
taicat_modifiedimage, but the derived Calculation rows are NOT refreshed. This
script finds the edits made on/after a start date, figures out which
(deployment, year, month) calculation cells they touch, and recomputes them via
taicat.utils.save_calculation (the same path used by scripts/calc-data.py).

It also handles the "stale species" case: save_calculation only (re)writes rows
for species that currently have images, so a species that was edited *away* would
otherwise keep an outdated Calculation row. For every species an edit mentions
(old or new value) that no longer has any image in the cell, the matching
Calculation rows are deleted.

Cell selection: an image belongs to the calculation cell of its *Taiwan-local*
month, because Deployment.calculate() defines each month window in TW time. The
cell is taken from the image's CURRENT deployment + datetime (the edit UI locks
deployment and datetime, so only species/annotation values change).

Usage:
  python scripts/recalc-modified-images.py --start-date 2026-01-01
  python scripts/recalc-modified-images.py --start-date 2026-01-01 --dry-run
"""

import argparse
import datetime as dt
import os
import sys
from calendar import monthrange

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.utils.timezone import make_aware

from taicat.models import (
    Calculation,
    Deployment,
    Image,
    ModifiedImage,
    timezone_tw_to_utc,
    timezone_utc_to_tw,
)
from taicat.utils import save_calculation


def month_window(year, month):
    """Return (day_start, day_end) matching Deployment.calculate()'s TW month window."""
    day_start = make_aware(timezone_tw_to_utc(dt.datetime(year, month, 1)))
    day_end = day_start + dt.timedelta(days=monthrange(year, month)[1])
    return day_start, day_end


def present_species(deployment_id, year, month):
    """Species that currently have (non-duplicated) images in the cell's TW month window."""
    day_start, day_end = month_window(year, month)
    rows = (
        Image.objects
        .filter(deployment_id=deployment_id, datetime__range=[day_start, day_end])
        .exclude(is_duplicated='Y')
        .values_list('species', flat=True)
        .distinct()
    )
    return {s.strip() for s in rows if s and s.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--start-date', required=True,
                        help='Recompute edits with last_updated >= this date (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Report affected cells and species without writing/deleting')
    args = parser.parse_args()

    try:
        start_date = dt.datetime.strptime(args.start_date, '%Y-%m-%d').date()
    except ValueError:
        parser.error('--start-date must be YYYY-MM-DD')

    modified = ModifiedImage.objects.filter(last_updated__gte=start_date)
    print(f'found {modified.count()} ModifiedImage record(s) since {start_date}')

    # cell -> set of species names mentioned by edits (old + new values)
    cells = {}
    missing = 0
    for mi in modified.iterator():
        img = (
            Image.objects
            .filter(id=mi.image_id)
            .values('deployment_id', 'datetime')
            .first()
        )
        if not img or not img['deployment_id'] or not img['datetime']:
            missing += 1
            continue
        tw = timezone_utc_to_tw(img['datetime'])
        key = (img['deployment_id'], tw.year, tw.month)
        mentioned = cells.setdefault(key, set())
        for value in (mi.species, mi.modified_species):
            if value and value.strip():
                mentioned.add(value.strip())

    if missing:
        print(f'skipped {missing} edit(s) whose image is gone or has no deployment/datetime')
    print(f'{len(cells)} affected calculation cell(s)')

    dep_cache = {}
    for (dep_id, year, month), mentioned in sorted(cells.items()):
        dep = dep_cache.get(dep_id)
        if dep is None:
            dep = dep_cache[dep_id] = Deployment.objects.filter(pk=dep_id).first()
        if dep is None:
            print(f'  [skip] deployment {dep_id} not found ({year}-{month:02d})')
            continue

        present = present_species(dep_id, year, month)
        recalc = sorted(mentioned & present)
        stale = sorted(mentioned - present)
        print(f'  deployment {dep_id} {year}-{month:02d} '
              f'recalc={recalc} delete_stale={stale}')

        if args.dry_run:
            continue

        if recalc:
            save_calculation(recalc, year, month, dep)
        if stale:
            day_start, _ = month_window(year, month)
            for sp in stale:
                Calculation.objects.filter(
                    deployment=dep,
                    datetime_from=day_start,
                    species=sp,
                ).delete()

    print('dry run complete (no changes written)' if args.dry_run else 'done')


if __name__ == '__main__':
    main()
