import json
import time
from datetime import datetime, timedelta

from django.db.models import Count
from django.core.cache import caches
from django.core.cache import cache
from django.utils.timezone import make_aware

from taicat.models import Image, Project, Deployment, Calculation
from taicat.utils import save_calculation

def calc_by_detail(did, year, month, working_days, deployment):
    rows = []
    query_ym = Image.objects.filter(
        deployment_id=did,
        datetime__year=year,
        datetime__month=month,
    )
    by_species = query_ym.values('species').annotate(count=Count('species'))
    sp_list = []
    for sp in by_species:
        if sp := sp['species'].strip():
            sp_list.append(sp)

    if sp_list:
        save_calculation(
            sp_list,
            #make_aware(datetime(year, month, 1)),
            #make_aware(datetime(year, month, len(working_days))+timedelta(seconds=-1)),
            year,
            month,
            deployment)
        #print(did, year, month, deployment)

    return rows

dep_count = 0
proj_count = 0
#for project in Project.objects.all():
for project in Project.objects.filter(id=329).all():
    print(project.id, project, '=================')
    if stats := project.count_stats():
        proj_count += 1
        begin = time.time()
        for year_str, value in stats['years'].items():
            for sa in value:
                for d in sa['items']:
                    if dep_id := d.get('id', ''):
                        dep = Deployment.objects.get(pk=dep_id)
                        print(dep)
                        dep_count += 1
                        for m in d['items']:
                            detail = json.loads(m[1])
                            calc_by_detail(d['id'], detail[0], detail[1], detail[6], dep)

print(proj_count, dep_count)


'''
SP = '山羌'
#im_list = Image.objects.filter(species=SP, datetime__gte=datetime(2022,11,1), datetime__lt=datetime(2022,12,1), deployment_id=13909).all()
#for i in im_list:
#    print(i.id, i.datetime)
dep = Deployment.objects.get(id=13909)
#print(dep.count_working_day(2022, 11))
#res = dep.calculate(2022, 12, '山羌', 60, 60)
#res = dep.calculate(2023, 1, '山羌', 60, 60)
#print(res)
save_calculation(['山羌'], 2022, 11, dep)
save_calculation(['山羌'], 2022, 12, dep)
#save_calculation(['山羌'], 2023, 1, dep)
'''
