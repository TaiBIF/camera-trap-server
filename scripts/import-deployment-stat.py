from taicat.utils import find_deployment_working_day
from taicat.models import Deployment, DeploymentStat

deps = Deployment.objects.filter(project_id=287).all()
print(len(deps))
year_list = range(2002, 2021)
for year in year_list:
    for month in range(1, 13):
        print (year, month,'-------------')
        for d in deps:
            r = find_deployment_working_day(year, month, d.id)
            #print(r, d.id, year, month)
            cnt = sum(r[0])
            if cnt > 0:
                ds = DeploymentStat(
                    project_id=d.project_id,
                    studyarea_id=d.study_area_id,
                    deployment_id=d.id,
                    year=year,
                    month=month,
                    count_working_hour=cnt*24,
                    session='month'
                )
                ds.save()
