"""
Delete upload folder data by folder_name.

Deletes: S3 objects, Images, UploadNotification, UploadHistory, DeploymentJournal.

Usage:
  python scripts/delete_upload_folder.py some_folder
  python scripts/delete_upload_folder.py --file folders.txt
  python scripts/delete_upload_folder.py --dry-run some_folder
"""

import argparse
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

import boto3
from django.conf import settings
from taicat.models import DeploymentJournal, Image
from base.models import UploadHistory, UploadNotification


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name='ap-northeast-1',
    )


def delete_s3_image(s3_client, image_uuid, dry_run=False):
    for suffix in ['l', 'm', 'x', 'q']:
        object_key = f'{image_uuid}-{suffix}.jpg'
        response = s3_client.list_object_versions(
            Bucket=settings.AWS_S3_BUCKET, Prefix=object_key
        )
        versions = response.get('Versions', []) + response.get('DeleteMarkers', [])
        for version in versions:
            version_id = version['VersionId']
            if dry_run:
                print(f"    [DRY-RUN] would delete S3 {object_key} version {version_id}")
            else:
                print(f"    Deleting S3 {object_key} version {version_id}")
                s3_client.delete_object(
                    Bucket=settings.AWS_S3_BUCKET,
                    Key=object_key,
                    VersionId=version_id,
                )
                s3_client.delete_object(
                    Bucket=settings.AWS_S3_BUCKET,
                    Key=object_key,
                )


def delete_folder_by_dj(dj, s3_client, dry_run=False):
    print(f"\n  Deleting deployment_journal id={dj.id}, folder={dj.folder_name}")

    # 1. Delete images + S3
    images = Image.objects.filter(deployment_journal_id=dj.id)
    img_count = images.count()
    print(f"  Images to delete: {img_count}")
    for img in images:
        delete_s3_image(s3_client, img.image_uuid, dry_run)
        if dry_run:
            print(f"    [DRY-RUN] would delete Image id={img.id}")
        else:
            img.delete()

    # 2. Delete UploadHistory + UploadNotification
    upload_histories = UploadHistory.objects.filter(deployment_journal_id=dj.id)
    for uh in upload_histories:
        notif_count = UploadNotification.objects.filter(upload_history_id=uh.id).count()
        if dry_run:
            print(f"    [DRY-RUN] would delete {notif_count} UploadNotification(s) for UploadHistory id={uh.id}")
            print(f"    [DRY-RUN] would delete UploadHistory id={uh.id}")
        else:
            UploadNotification.objects.filter(upload_history_id=uh.id).delete()
            print(f"    Deleted {notif_count} UploadNotification(s) for UploadHistory id={uh.id}")
            uh.delete()
            print(f"    Deleted UploadHistory id={uh.id}")

    if not upload_histories.exists():
        print(f"    No UploadHistory found")

    # 3. Delete DeploymentJournal
    dj_id = dj.id
    if dry_run:
        print(f"    [DRY-RUN] would delete DeploymentJournal id={dj_id}")
    else:
        dj.delete()
        print(f"    Deleted DeploymentJournal id={dj_id}")


def delete_folder(folder_name, s3_client, dry_run=False):
    djs = DeploymentJournal.objects.filter(folder_name=folder_name).all()

    if not djs:
        print(f"\n[NOT FOUND] folder_name='{folder_name}'")
        return

    if len(djs) > 1:
        print(f"\n[WARNING] Found {len(djs)} journals for '{folder_name}', deleting the last one")
        dj = djs[len(djs) - 1]
        delete_folder_by_dj(dj, s3_client, dry_run)
    else:
        delete_folder_by_dj(djs[0], s3_client, dry_run)


def main():
    parser = argparse.ArgumentParser(description='Delete upload folder data by folder_name')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('folder_name', nargs='?', help='Single folder name to delete')
    group.add_argument('--file', '-f', help='File with folder names (one per line)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    args = parser.parse_args()

    folders = []
    if args.file:
        with open(args.file) as f:
            folders = [line.strip() for line in f if line.strip()]
    else:
        folders = [args.folder_name]

    if args.dry_run:
        print("[DRY-RUN MODE] No data will be deleted.\n")

    print(f"Processing {len(folders)} folder(s)...")

    s3_client = get_s3_client()
    for folder in folders:
        delete_folder(folder, s3_client, args.dry_run)

    print(f"\n{'='*60}")
    print("Done.")


if __name__ == '__main__':
    main()
