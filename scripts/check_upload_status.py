"""
Check upload status by folder_name.

Usage:
  # Single folder
  python manage.py shell < scripts/check_upload_status.py --folder_name "some_folder"

  # Or run directly with Django setup:
  python scripts/check_upload_status.py some_folder
  python scripts/check_upload_status.py --file folders.txt

  folders.txt should have one folder_name per line.

  # CSV/TSV mode: input must have a 'folder_name' header column.
  # Output is a copy of the input rows with status columns appended.
  # Delimiter is auto-detected (.tsv/.tab -> tab, else sniffed), or forced with -d.
  python scripts/check_upload_status.py --csv input.csv
  python scripts/check_upload_status.py --csv input.tsv
  python scripts/check_upload_status.py --csv input.csv --out output.csv
  python scripts/check_upload_status.py --csv input.txt -d tab
"""

import argparse
import csv
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


# Columns appended to the source CSV.
STATUS_HEADERS = [
    'deployment_journal_id',
    'created',
    'num_of_images',
    'uploaded_ratio',
    'uploader',
    'client_version',
    'client_hostname',
    'upload_uuid',
]


def _journal_status(j):
    """Build a STATUS_HEADERS dict for one DeploymentJournal."""
    counts = (
        Image.objects
        .filter(deployment_journal_id=j.id)
        .values('has_storage')
        .annotate(count=Count('id'))
    )
    total = sum(row['count'] for row in counts)
    uploaded = sum(row['count'] for row in counts if row['has_storage'] == 'Y')
    if total > 0:
        ratio = f"{uploaded}/{total} ({uploaded / total * 100:.1f}%)"
    else:
        ratio = f"{uploaded}/0"

    return {
        'deployment_journal_id': j.id,
        'created': j.created.isoformat() if j.created else '',
        'num_of_images': j.num_of_images if j.num_of_images is not None else '',
        'uploaded_ratio': ratio,
        'uploader': j.uploader.name if j.uploader else '',
        'client_version': j.client_version or '',
        'client_hostname': j.client_hostname or '',
        'upload_uuid': j.upload_uuid or '',
    }


def get_folder_status(folder_name):
    """Return a list of STATUS_HEADERS dicts for a folder_name.

    A folder_name may have multiple uploads (one DeploymentJournal each);
    each is returned as its own dict so every upload shows up in the output.
    Returns a single NOT_FOUND dict when no journal matches.
    """
    journals = (
        DeploymentJournal.objects
        .filter(folder_name=folder_name)
        .order_by('created')
    )

    if not journals.exists():
        status = {h: '' for h in STATUS_HEADERS}
        status['deployment_journal_id'] = 'NOT_FOUND'
        return [status]

    return [_journal_status(j) for j in journals]


def detect_delimiter(input_path):
    """Tab for .tsv/.tab files, else sniff the header line (comma fallback)."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext in ('.tsv', '.tab'):
        return '\t'
    with open(input_path, newline='', encoding='utf-8-sig') as f:
        first_line = f.readline()
    if '\t' in first_line and first_line.count('\t') >= first_line.count(','):
        return '\t'
    return ','


def check_csv(input_path, output_path, delimiter=None):
    if delimiter is None:
        delimiter = detect_delimiter(input_path)
    print(f"Delimiter: {'TAB' if delimiter == chr(9) else repr(delimiter)}")

    with open(input_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None or 'folder_name' not in reader.fieldnames:
            sys.exit(f"ERROR: input file must have a 'folder_name' header. Got: {reader.fieldnames}")
        rows = list(reader)
        src_headers = list(reader.fieldnames)

    # Avoid clobbering source columns if they collide with status headers.
    out_headers = src_headers + [h for h in STATUS_HEADERS if h not in src_headers]

    print(f"Checking {len(rows)} row(s) from {input_path}...")
    written = 0
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=out_headers, delimiter=delimiter)
        writer.writeheader()
        for i, row in enumerate(rows, 1):
            folder = (row.get('folder_name') or '').strip()
            statuses = get_folder_status(folder) if folder else [{h: '' for h in STATUS_HEADERS}]
            # One output row per upload; the source columns are repeated.
            for status in statuses:
                out_row = dict(row)
                out_row.update(status)
                writer.writerow(out_row)
                written += 1
            ids = ', '.join(str(s.get('deployment_journal_id')) for s in statuses)
            note = f" ({len(statuses)} uploads)" if len(statuses) > 1 else ''
            print(f"  [{i}/{len(rows)}] {folder} -> {ids}{note}")

    print(f"\nWrote: {output_path} ({written} row(s) from {len(rows)} input row(s))")


def main():
    parser = argparse.ArgumentParser(description='Check upload status by folder_name')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('folder_name', nargs='?', help='Single folder name to check')
    group.add_argument('--file', '-f', help='File with folder names (one per line)')
    group.add_argument('--csv', help="Input csv/tsv with a 'folder_name' header column")
    parser.add_argument('--out', '-o', help='Output path (csv mode). Default: <input>_status<ext>')
    parser.add_argument('--delimiter', '-d', choices=['comma', 'tab'],
                        help='Force input/output delimiter (csv mode). Default: auto-detect')
    args = parser.parse_args()

    if args.csv:
        if args.out:
            output_path = args.out
        else:
            base, ext = os.path.splitext(args.csv)
            output_path = f"{base}_status{ext or '.csv'}"
        delim = {'comma': ',', 'tab': '\t'}.get(args.delimiter)
        check_csv(args.csv, output_path, delimiter=delim)
        print(f"\n{'='*60}")
        print("Done.")
        return

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
