from taicat.models import *
from django.db import connection
import pandas as pd
from django.utils import timezone

now = timezone.now()
with connection.cursor() as cursor:
    query = """SELECT EXTRACT (year FROM datetime) as year, count(distinct(image_uuid)) as count
    FROM taicat_image
    GROUP BY year"""
    cursor.execute(query)
    data_growth_image = cursor.fetchall()
    data_growth_image = pd.DataFrame(data_growth_image, columns=['year', 'num_image']).sort_values('year')
    year_min, year_max = int(data_growth_image.year.min()), int(data_growth_image.year.max())
    year_gap = pd.DataFrame([i for i in range(year_min, year_max+1)], columns=['year'])
    data_growth_image = year_gap.merge(data_growth_image, how='left').fillna(0)
    data_growth_image['cumsum'] = data_growth_image.num_image.cumsum()
    data_growth_image = data_growth_image.drop(columns=['num_image'])


for i in data_growth_image.index:
    new = HomePageStat(
        count=data_growth_image.loc[i, 'cumsum'],
        year=data_growth_image.loc[i, 'year'],
        last_updated=now
    )
    new.save()
    # data_growth_image = list(
    #     data_growth_image.itertuples(index=False, name=None))

# deprecated #
# with connection.cursor() as cursor:
#     query = """
#             SELECT MIN(EXTRACT (year FROM datetime)) as year, deployment_id FROM taicat_image
#             GROUP BY deployment_id
#     """
#     cursor.execute(query)
#     data_growth_deployment = cursor.fetchall()
#     data_growth_deployment = pd.DataFrame(data_growth_deployment, columns=[
#         'year', 'deployment_id']).sort_values('year')
#     data_growth_deployment = data_growth_deployment.groupby(
#         ['year'], as_index=False).count()
#     data_growth_deployment = year_gap.merge(
#         data_growth_deployment, how='left').fillna(0)
#     data_growth_deployment['cumsum'] = data_growth_deployment.deployment_id.cumsum(
#     )
#     data_growth_deployment = data_growth_deployment.drop(
#         columns=['deployment_id'])

# for i in data_growth_deployment.index:
#     new = HomePageStat(
#         count=data_growth_deployment.loc[i, 'cumsum'],
#         year=data_growth_deployment.loc[i, 'year'],
#         type='deployment',
#         last_updated=now
#     )
#     new.save()

# ---------- project ---------- #
now = timezone.now()
with connection.cursor() as cursor:
    q = "SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                    EXTRACT (year from taicat_project.start_date)::int, \
                    taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea \
                    FROM taicat_project \
                    LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                    GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                    ORDER BY taicat_project.start_date DESC;"
    cursor.execute(q)
    project_info = cursor.fetchall()
    project_info = pd.DataFrame(project_info, columns=['id', 'name', 'keyword', 'start_year', 'funding_agency', 'num_studyarea'])

project_info['num_data'] = 0
project_info['num_deployment'] = 0

for i in project_info.id:
    image_c = Image.objects.filter(project_id=i).count()
    dep_c = Deployment.objects.filter(project_id=i).count()
    project_info.loc[project_info['id'] == i, 'num_data'] = image_c
    project_info.loc[project_info['id'] == i, 'num_deployment'] = dep_c

project_info = project_info[['id', 'name', 'keyword', 'start_year', 'funding_agency', 'num_studyarea', 'num_deployment', 'num_data']]

for i in project_info.index:
    print(i)
    latest_date = None
    earliest_date = None
    image_objects = Image.objects.filter(project_id=project_info.loc[i, 'id'])
    if image_objects.exists():
        latest_date = image_objects.latest('datetime').datetime
        earliest_date = image_objects.earliest('datetime').datetime
        # ProjectStat.objects.filter(project_id=project_info.loc[i, 'id']).update(latest_date=latest_date, earliest_date=earliest_date)
    new = ProjectStat(
        project_id=project_info.loc[i, 'id'],
        num_sa=project_info.loc[i, 'num_studyarea'],
        num_deployment=project_info.loc[i, 'num_deployment'],
        num_data=project_info.loc[i, 'num_data'],
        last_updated=now,
        latest_date=latest_date,
        earliest_date=earliest_date,
    )
    new.save()
