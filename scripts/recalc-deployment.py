"""
Recalculate Calculation data for whole deployments, pruning stale species rows.

Use this after operations that change which images belong to a deployment but do
NOT log to ModifiedImage and do NOT refresh Calculation, e.g.:
  - scripts/swap-deployment.py  -> recalc BOTH the source and target deployments
  - scripts/delete_upload_folder.py -> recalc the deployment(s) of the deleted folder

It recomputes every (year, month) cell that currently has images or already has a
Calculation row (so counts are corrected on both sides of a move and emptied
months drop to zero), AND prunes orphan species: rows for a non-default species
that no longer has any image anywhere in the deployment (e.g. a typo species
fixed by an edit) are deleted. Default species and species still present in other
months keep their zero baselines -- unlike a naive delete, this does not wipe the
intentional zero rows the analysis relies on.

Selection (combine freely; all given deployments are processed):
  --deployment-id <id>          repeatable
  --from-deployment <id>        convenience for a swap's source
  --to-deployment <id>          convenience for a swap's target

Options:
  --year <YYYY>     limit to a single year (default: all years with data)
  --dry-run         report what would change without writing/deleting

Examples:
  # after a swap from 13909 to 14001
  python scripts/recalc-deployment.py --from-deployment 13909 --to-deployment 14001
  # after deleting a folder whose images were on deployment 13896
  python scripts/recalc-deployment.py --deployment-id 13896 --dry-run
"""

import argparse
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from taicat.models import Deployment
from taicat.utils import recalc_deployment


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--deployment-id', type=int, action='append', default=[],
                        help='deployment id to recalc (repeatable)')
    parser.add_argument('--from-deployment', type=int, help='swap source deployment id')
    parser.add_argument('--to-deployment', type=int, help='swap target deployment id')
    parser.add_argument('--year', type=int, help='limit to a single year (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='report changes without writing/deleting')
    args = parser.parse_args()

    dep_ids = list(dict.fromkeys(
        args.deployment_id
        + ([args.from_deployment] if args.from_deployment else [])
        + ([args.to_deployment] if args.to_deployment else [])
    ))
    if not dep_ids:
        parser.error('give at least one of --deployment-id / --from-deployment / --to-deployment')

    print(f'deployments to recalc: {dep_ids}'
          f'{f" (year={args.year})" if args.year else ""}'
          f'{" [DRY RUN]" if args.dry_run else ""}')

    for dep_id in dep_ids:
        dep = Deployment.objects.filter(pk=dep_id).first()
        if not dep:
            print(f'\n[skip] deployment {dep_id} not found')
            continue
        print(f'\ndeployment {dep_id} "{dep.name}" (studyarea={dep.study_area_id}, '
              f'project={dep.project_id})')
        cell_results, (orphans, n_orphan_rows) = recalc_deployment(
            dep, year=args.year, dry_run=args.dry_run)
        verb = 'would prune' if args.dry_run else 'pruned'
        print(f'  orphan species {verb}: {orphans} ({n_orphan_rows} row(s))')
        if not cell_results:
            print('  no cells with data')
            continue
        for year, month, recompute in cell_results:
            print(f'  {year}-{month:02d}  recompute={recompute}')

    print('\ndry run complete (no changes written)' if args.dry_run else '\ndone')


if __name__ == '__main__':
    main()
