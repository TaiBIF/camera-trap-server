from taicat.models import Project, DeploymentJournal
from django.db.models import (
    Max,
    Min,
)
PROJECT_ID = 287
project = Project.objects.get(pk=PROJECT_ID)

#project.find_and_create_deployment_journal_gap()

#project.get_or_count_stats(force=True)
c = 0
d = {}
rows = project.get_deployment_list()
for sa in rows:
    for d in sa['deployments']:
        #print (d)
        d['deployment_id'] = d['name']
        c += 1
print(c)

year_list = range(2002, 2021)
for year in year_list:
    for month in range(1, 13):
        print (year, month,'-------------')
        for x in d:
            query_image = Image.objects.filter(
                deployment_id=x,
                datetime__year=year,
                datetime__month=month,
            )
            by_species = query_image.values('species').annotate(count=Count('species'))
            for i in by_species:
