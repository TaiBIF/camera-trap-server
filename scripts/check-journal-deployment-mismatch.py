"""
Find images (project 329) where DeploymentJournal.deployment_id differs
from Image.deployment_id when joined on folder_name.

Usage:
  python scripts/check-journal-deployment-mismatch.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.db import connection

PROJECT_ID = 329

sql = """
SELECT
    dj.folder_name,
    dj.id                AS journal_id,
    dj.deployment_id     AS journal_deployment_id,
    i.deployment_id      AS image_deployment_id,
    i.deployment_journal_id AS image_journal_id,
    COUNT(i.id)          AS image_count
FROM taicat_deploymentjournal dj
JOIN taicat_image i
    ON  i.folder_name  = dj.folder_name
    AND i.project_id   = %s
WHERE dj.project_id = %s
  AND dj.deployment_id IS DISTINCT FROM i.deployment_id
GROUP BY
    dj.folder_name,
    dj.id,
    dj.deployment_id,
    i.deployment_id,
    i.deployment_journal_id
ORDER BY dj.folder_name
"""

with connection.cursor() as cursor:
    cursor.execute(sql, [PROJECT_ID, PROJECT_ID])
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]

if not rows:
    print('No mismatches found.')
else:
    print(f'Found {len(rows)} mismatch group(s):\n')
    header = '  '.join(f'{c:<30}' if 'folder' in c else f'{c:<25}' for c in cols)
    print(header)
    print('-' * len(header))
    for row in rows:
        print('  '.join(f'{str(v):<30}' if 'folder' in cols[i] else f'{str(v):<25}' for i, v in enumerate(row)))
