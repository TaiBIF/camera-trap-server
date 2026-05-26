"""
Swap (reassign) the 相機位置 (deployment) of a set of images.

Selects images by one of three mutually-exclusive ways and re-points them to
a target deployment, keeping the denormalized studyarea_id / project_id in
sync with that deployment. Dry-run by default; pass --commit to write.

The DeploymentJournal rows the selected images belong to (via
Image.deployment_journal_id) are moved onto the target deployment as well:
their deployment_id / studyarea_id are updated to match. This keeps each
journal consistent with its images. No extra flag is needed.

Selection modes (choose exactly one):
  --from-deployment <id>          all images currently on this deployment
  --project <id> --folder <name>  images of this project in this folder
                                  (--folder repeatable)
  --image-ids 1,2,3               an explicit comma-separated list

Target:
  --to-deployment <id>            the deployment to move the images onto

Options:
  --commit           perform the update inside a transaction
                     (without it, nothing is written)

Examples:
  python scripts/swap-deployment.py --from-deployment 13909 --to-deployment 14001
  python scripts/swap-deployment.py --project 329 --folder ABC0001 --to-deployment 14001 --commit
  python scripts/swap-deployment.py --image-ids 1,2,3 --to-deployment 14001 --commit

Cross-project moves are refused: per-project species/stat/folder counts would
need recalculation. Use the image edit UI (api/edit_image) for those.
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

from taicat.models import Deployment, DeploymentJournal, Image


def parse_args():
    p = argparse.ArgumentParser(description='Swap the deployment (相機位置) of images.')
    p.add_argument('--from-deployment', type=int, help='source deployment id (move all its images)')
    p.add_argument('--project', type=int, help='project id (use with --folder)')
    p.add_argument('--folder', action='append', default=[], help='folder_name (repeatable, use with --project)')
    p.add_argument('--image-ids', help='explicit comma-separated image ids')
    p.add_argument('--to-deployment', type=int, required=True, help='target deployment id')
    p.add_argument('--commit', action='store_true', help='write changes (default: dry run)')
    return p.parse_args()


def select_images(args):
    """Return (queryset, human_description) for the chosen selection mode."""
    modes = [
        args.from_deployment is not None,
        bool(args.project and args.folder),
        bool(args.image_ids),
    ]
    if sum(modes) != 1:
        sys.exit('ERROR: choose exactly one selection mode: --from-deployment, '
                 '(--project + --folder), or --image-ids.')

    if args.from_deployment is not None:
        qs = Image.objects.filter(deployment_id=args.from_deployment)
        return qs, f'images on deployment {args.from_deployment}'

    if args.project and args.folder:
        qs = Image.objects.filter(project_id=args.project, folder_name__in=args.folder)
        return qs, f'images of project {args.project} in folders {args.folder}'

    ids = [int(x) for x in args.image_ids.split(',') if x.strip()]
    qs = Image.objects.filter(id__in=ids)
    return qs, f'{len(ids)} explicit image id(s)'


def main():
    args = parse_args()

    target = Deployment.objects.filter(id=args.to_deployment).select_related('study_area', 'project').first()
    if not target:
        sys.exit(f'ERROR: target deployment {args.to_deployment} not found.')

    qs, desc = select_images(args)
    total = qs.count()
    if total == 0:
        print(f'No images matched ({desc}). Nothing to do.')
        return

    # Guard: refuse cross-project moves (per-project stats would drift).
    src_projects = set(qs.order_by('project_id').values_list('project_id', flat=True).distinct())
    if src_projects - {target.project_id}:
        sys.exit(
            f'ERROR: cross-project move refused. Selected images belong to project(s) '
            f'{sorted(src_projects)} but target deployment {target.id} is in project '
            f'{target.project_id}. Per-project species/stat/folder counts would need '
            f'recalculation; use the image edit UI (api/edit_image) for cross-project moves.'
        )

    print(f'Target deployment : {target.id} "{target.name}" '
          f'(study_area={target.study_area_id}, project={target.project_id})')
    print(f'Selection         : {desc}')
    print(f'Matched images    : {total}')

    # Show current spread of (deployment, studyarea) being moved.
    spread = (qs.values('deployment_id', 'studyarea_id')
                .order_by('deployment_id')
                .distinct())
    print('Current (deployment_id, studyarea_id) -> target:')
    for s in spread:
        n = qs.filter(deployment_id=s['deployment_id'], studyarea_id=s['studyarea_id']).count()
        print(f'  ({s["deployment_id"]}, {s["studyarea_id"]})  x{n}  ->  '
              f'({target.id}, {target.study_area_id})')

    now = timezone.now()
    update_fields = {
        'deployment_id': target.id,
        'studyarea_id': target.study_area_id,
        'project_id': target.project_id,
        'last_updated': now,
    }

    # Move the journals these images belong to onto the target deployment too,
    # so each DeploymentJournal stays consistent with its images.
    journal_ids = set(
        qs.exclude(deployment_journal_id__isnull=True)
          .order_by('deployment_journal_id')
          .values_list('deployment_journal_id', flat=True)
          .distinct()
    )
    journal_qs = DeploymentJournal.objects.filter(id__in=journal_ids)
    print(f'Journals to move  : {len(journal_ids)} '
          f'(set deployment_id -> {target.id}, studyarea_id -> {target.study_area_id})')

    # Warn if a journal also serves images outside this selection: moving it
    # would leave those images mismatched against their journal's deployment.
    for jid in sorted(journal_ids):
        total_j = Image.objects.filter(deployment_journal_id=jid).count()
        in_sel = qs.filter(deployment_journal_id=jid).count()
        if total_j > in_sel:
            print(f'  WARN: journal {jid} has {total_j - in_sel} image(s) NOT in this '
                  f'selection; they would no longer match their journal deployment.')

    if not args.commit:
        print('\nDRY RUN — no changes written. Re-run with --commit to apply.')
        return

    with transaction.atomic():
        n = qs.update(**update_fields)
        j = journal_qs.update(
            deployment_id=target.id,
            studyarea_id=target.study_area_id,
            last_updated=now,
        )
    print(f'\nDONE: updated {n} image(s), moved {j} journal(s) to deployment {target.id}.')


if __name__ == '__main__':
    main()
