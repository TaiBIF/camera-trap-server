"""
Check upload status by folder_name.

Usage:
  # Single folder
  python manage.py shell < scripts/check_upload_status.py --folder_name "some_folder"

  # Or run directly with Django setup:
  python scripts/check_upload_status.py some_folder
  python scripts/check_upload_status.py --file folders.txt

  folders.txt should have one folder_name per line.
"""

import argparse
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.db.models import Count, Q
from taicat.models import DeploymentJournal, Image
from base.models import UploadHistory


def check_folder(folder_name):
    journals = DeploymentJournal.objects.filter(folder_name=folder_name)

    if not journals.exists():
        print(f"\n[NOT FOUND] folder_name='{folder_name}'")
        return

    for j in journals:
        print(f"\n{'='*60}")
        print(f"folder_name: {j.folder_name}")
        print(f"  deployment_journal_id: {j.id}")
        print(f"  project: {j.project_id}")
        print(f"  deployment: {j.deployment_id}")
        print(f"  upload_status: {j.upload_status}")
        print(f"  num_of_images (expected): {j.num_of_images}")
        print(f"  created: {j.created}")
        uploader_name = j.uploader.name if j.uploader else 'N/A'
        print(f"  uploader: {uploader_name} (id={j.uploader_id})")
        print(f"  client_version: {j.client_version}")

        # Count images grouped by has_storage
        image_counts = (
            Image.objects
            .filter(deployment_journal_id=j.id)
            .values('has_storage')
            .annotate(count=Count('id'))
            .order_by('has_storage')
        )

        total = 0
        print(f"  --- image counts by has_storage ---")
        for row in image_counts:
            print(f"    has_storage='{row['has_storage']}': {row['count']}")
            total += row['count']

        # Count images with species filled
        images_qs = Image.objects.filter(deployment_journal_id=j.id)
        with_species = images_qs.exclude(species='').count()
        without_species = images_qs.filter(species='').count()
        print(f"  --- species check ---")
        print(f"    with species: {with_species}")
        print(f"    without species (empty): {without_species}")

        print(f"  total images in db: {total}")
        expected = j.num_of_images or 0
        if expected > 0:
            diff = expected - total
            pct = total / expected * 100
            status = "OK" if diff == 0 else f"MISSING {diff}"
            print(f"  compare: {total}/{expected} ({pct:.1f}%) [{status}]")
        else:
            print(f"  compare: expected=N/A")

        # UploadHistory
        uh = UploadHistory.objects.filter(deployment_journal_id=j.id).first()
        if uh:
            print(f"  --- upload_history ---")
            print(f"    status: {uh.status}")
            print(f"    species_error: {uh.species_error}")
            print(f"    upload_error: {uh.upload_error}")
            print(f"    last_updated: {uh.last_updated}")
        else:
            print(f"  --- upload_history: N/A ---")


def main():
    parser = argparse.ArgumentParser(description='Check upload status by folder_name')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('folder_name', nargs='?', help='Single folder name to check')
    group.add_argument('--file', '-f', help='File with folder names (one per line)')
    args = parser.parse_args()

    folders = []
    if args.file:
        with open(args.file) as f:
            folders = [line.strip() for line in f if line.strip()]
    else:
        folders = [args.folder_name]

    print(f"Checking {len(folders)} folder(s)...")

    for folder in folders:
        check_folder(folder)

    print(f"\n{'='*60}")
    print("Done.")


if __name__ == '__main__':
    main()
