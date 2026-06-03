"""
Recalculate Calculation data affected by image edits recorded in ModifiedImage.

When a user edits an image (species / life_stage / ... ) the change is logged in
taicat_modifiedimage, but the derived Calculation rows are NOT refreshed. This
script finds the edits made on/after a start date, figures out which
(deployment, year, month) calculation cells they touch, and recomputes each cell
via taicat.utils.recalc_deployment_month -- refreshing every species in the cell
to its current value (a species edited away is recomputed to image_count 0,
matching the zero-baseline convention). To also delete leftover rows for typo /
removed species that no longer appear anywhere in a deployment, run
scripts/recalc-deployment.py for that deployment.

Cell selection: an image belongs to the calculation cell of its *Taiwan-local*
month, because Deployment.calculate() defines each month window in TW time. The
cell is taken from the image's CURRENT deployment + datetime (the edit UI locks
deployment and datetime, so only species/annotation values change). Edits that
moved an image to a different deployment/month before that lock are reconciled at
the image's current cell only.

Usage:
  python scripts/recalc-modified-images.py --start-date 2026-01-01
  python scripts/recalc-modified-images.py --start-date 2026-01-01 --dry-run
"""

import argparse
import datetime as dt
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from taicat.models import Deployment, Image, ModifiedImage, timezone_utc_to_tw
from taicat.utils import recalc_deployment_month


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

    # distinct (deployment_id, year, month) cells touched by the edits
    cells = set()
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
        cells.add((img['deployment_id'], tw.year, tw.month))

    if missing:
        print(f'skipped {missing} edit(s) whose image is gone or has no deployment/datetime')
    print(f'{len(cells)} affected calculation cell(s)')

    dep_cache = {}
    for dep_id, year, month in sorted(cells):
        dep = dep_cache.get(dep_id)
        if dep is None:
            dep = dep_cache[dep_id] = Deployment.objects.filter(pk=dep_id).first()
        if dep is None:
            print(f'  [skip] deployment {dep_id} not found ({year}-{month:02d})')
            continue

        recompute = recalc_deployment_month(dep, year, month, dry_run=args.dry_run)
        print(f'  deployment {dep_id} {year}-{month:02d} recompute={recompute}')

    print('dry run complete (no changes written)' if args.dry_run else 'done')


if __name__ == '__main__':
    main()
