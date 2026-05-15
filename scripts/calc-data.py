"""
Calculate deployment data, optionally scoped by year and/or deployment/studyarea.

Usage:
  python scripts/calc-data.py                                # all deployments, all years
  python scripts/calc-data.py --year 2024
  python scripts/calc-data.py --deployment-id 13909
  python scripts/calc-data.py --studyarea-id 1932 --year 2024

--deployment-id and --studyarea-id are mutually exclusive.
"""

import argparse
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.db.models import Count

from taicat.models import Image, Deployment
from taicat.utils import save_calculation


def calc_by_detail(deployment, year, month):
    by_species = (
        Image.objects
        .filter(deployment_id=deployment.id, datetime__year=year, datetime__month=month)
        .values('species')
        .annotate(count=Count('species'))
    )
    sp_list = [s for sp in by_species if (s := sp['species'].strip())]
    if sp_list:
        save_calculation(sp_list, year, month, deployment)


def years_with_data(deployment_id):
    rows = (
        Image.objects
        .filter(deployment_id=deployment_id)
        .dates('datetime', 'year')
    )
    return sorted({d.year for d in rows})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, help='Year to calculate (default: all years with data)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--deployment-id', type=int)
    group.add_argument('--studyarea-id', type=int)
    args = parser.parse_args()

    if args.deployment_id:
        deployments = Deployment.objects.filter(pk=args.deployment_id)
    elif args.studyarea_id:
        deployments = Deployment.objects.filter(study_area_id=args.studyarea_id)
    else:
        deployments = Deployment.objects.all()

    total = deployments.count()
    print(f'processing {total} deployment(s)')

    for i, dep in enumerate(deployments.iterator(), 1):
        years = [args.year] if args.year else years_with_data(dep.id)
        print(f'[{i}/{total}] deployment {dep.id} {dep} years={years}')
        for year in years:
            for month in range(1, 13):
                calc_by_detail(dep, year, month)


if __name__ == '__main__':
    main()
