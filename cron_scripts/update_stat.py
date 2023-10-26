from taicat.models import *
from django.db import connection
from django.utils import timezone
from django.db.models import Count, Max
import pandas as pd

# ---------- HOMEPAGE STAT ---------- #
now = timezone.now()
print('start HOMEPAGE STAT', now)

with connection.cursor() as cursor:
    query = """SELECT EXTRACT (year FROM i.datetime) as year, count(distinct(i.image_uuid)) as count
    FROM taicat_image i
    JOIN taicat_project p ON i.project_id = p.id
    WHERE p.mode = 'official'
    GROUP BY year"""
    cursor.execute(query)
    data_growth_image = cursor.fetchall()
    data_growth_image = pd.DataFrame(data_growth_image, columns=['year', 'num_image']).sort_values('year')
    year_min, year_max = int(data_growth_image.year.min()), int(data_growth_image.year.max())
    year_gap = pd.DataFrame([i for i in range(year_min, year_max+1)], columns=['year'])
    data_growth_image = year_gap.merge(data_growth_image, how='left').fillna(0)
    data_growth_image['cumsum'] = data_growth_image.num_image.cumsum()
    data_growth_image = data_growth_image.drop(columns=['num_image'])

# if exists, update; if not, create
for i in data_growth_image.index:
    if hps := HomePageStat.objects.filter(year=data_growth_image.loc[i, 'year']).first():
        # print('here')
        hps.count = data_growth_image.loc[i, 'cumsum']
        hps.last_updated = now
        hps.save()
    else:
        new = HomePageStat(
            count=data_growth_image.loc[i, 'cumsum'],
            year=data_growth_image.loc[i, 'year'],
            last_updated=now
        )
        new.save()

# ---------- PROJECT ---------- #
now = timezone.now()
print('start PROJECT STAT', now)
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
    latest_date = None
    earliest_date = None
    image_objects = Image.objects.filter(project_id=project_info.loc[i, 'id'])
    if image_objects.exists():
        query = f"select min(datetime), max(datetime) from taicat_image where project_id={project_info.loc[i, 'id']};"
        with connection.cursor() as cursor:
            cursor.execute(query)
            dates = cursor.fetchall()
        latest_date = dates[0][1]
        earliest_date = dates[0][0]
    if ps := ProjectStat.objects.filter(project_id=project_info.loc[i, 'id']).first():
        ps.num_sa = project_info.loc[i, 'num_studyarea']
        ps.num_deployment = project_info.loc[i, 'num_deployment']
        ps.num_data = project_info.loc[i, 'num_data']
        ps.last_updated = now
        ps.latest_date = latest_date
        ps.earliest_date = earliest_date
        ps.save()
    else:
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

# ---------- SPECIES ---------- #
now = timezone.now()
print('start SPECIES STAT', now)
query = Image.objects.filter(project__mode='official').values('species').annotate(total=Count('species')).order_by('-total')
for i in query:
    if sp := Species.objects.filter(name=i['species']).first():
        sp.count = i['total']
        sp.last_updated = now
        sp.save()
    else:
        sp = Species(name=i['species'], last_updated=now, count=i['total'])
        if i['species'] in Species.DEFAULT_LIST:
            sp.is_default = True
        sp.save()

# delete count = 0
Species.objects.filter(count=0).delete()

# ---------- PROJECTSPECIES ---------- #
now = timezone.now()
print('start PROJECT SPECIES', now)

for p in Project.objects.all().values('id'):
    query = Image.objects.filter(project_id=p['id']).values('species').annotate(total=Count('species')).order_by('-total')
    for i in query:
        if p_sp := ProjectSpecies.objects.filter(name=i['species'], project_id=p['id']).first():
            p_sp.count = i['total']
            p_sp.last_updated = now
            p_sp.save()
        else:
            p_sp = ProjectSpecies(
                name=i['species'],
                last_updated=now,
                count=i['total'],
                project_id=p['id'])
            p_sp.save()

# delete count = 0
ProjectSpecies.objects.filter(count=0).delete()

# ---------- IMAGE FOLDER ------------ #
now = timezone.now()
print('start IMAGE FOLDER', now)

for p in Project.objects.all().values('id'):
    f_names = []
    query = Image.objects.exclude(folder_name='').filter(project_id=p['id']).order_by('folder_name').distinct('folder_name').values('folder_name')
    for q in query:
        f_last_updated = Image.objects.filter(project_id=p['id'], folder_name=q['folder_name']).aggregate(Max('last_updated'))['last_updated__max']
        f_names += [q['folder_name']]
        if img_f := ImageFolder.objects.filter(folder_name=q['folder_name'], project_id=p['id']).first():
            img_f.folder_last_updated = f_last_updated
            img_f.last_updated = now
            img_f.save()
        else:
            img_f = ImageFolder(
                folder_name=q['folder_name'],
                folder_last_updated=f_last_updated,
                project_id=p['id'])
            img_f.save()
    # 確定imagefolder是不是有空的
    ImageFolder.objects.filter(project_id=p['id']).exclude(folder_name__in=f_names).delete()


# ---------- HOMEPAGE MAP ----------- #
import geopandas as gpd
from conf.settings import BASE_DIR
import os
import pygeos
#gpd.options.use_pygeos = True

print('start HOMEPAGE MAP', now)

species_list = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']

now = timezone.now()

#gpd.options.use_pygeos = True

geo_df = gpd.read_file(os.path.join(os.path.join(BASE_DIR, "static"),'map/COUNTY_MOI_1090820.shp'))

# 只選擇正式的資料

query = """
        SELECT d.longitude, d.latitude, d.id, d.geodetic_datum FROM taicat_deployment d
        JOIN taicat_project p ON d.project_id = p.id
        WHERE p.mode = 'official';
        """

with connection.cursor() as cursor:
    cursor.execute(query)
    d_df = cursor.fetchall()
    d_df = pd.DataFrame(d_df, columns=['longitude', 'latitude', 'did', 'geodetic_datum'])


# TODO 這邊會分成TWD97 & WGS84
d_df_wgs84 = d_df[d_df.geodetic_datum=='WGS84'].reset_index()
d_df_twd97 = d_df[d_df.geodetic_datum=='TWD97'].reset_index()


# d_df = pd.DataFrame(Deployment.objects.all().values('longitude','latitude','id', 'geodetic_datum'))

d_df_wgs84 = gpd.GeoDataFrame(d_df_wgs84,geometry=gpd.points_from_xy(d_df_wgs84.longitude,d_df_wgs84.latitude))
d_df_twd97 = gpd.GeoDataFrame(d_df_twd97,geometry=gpd.points_from_xy(d_df_twd97.longitude,d_df_twd97.latitude))

d_df_twd97 = d_df_twd97.set_crs(epsg=3826, inplace=True)
# moogoo: crs mismatch, 230726
#d_df_twd97 = d_df_twd97.to_crs(epsg=4326)
d_df_twd97 = d_df_twd97.to_crs(epsg=3824)


d_gdf = d_df_twd97.append(d_df_wgs84)

join = gpd.sjoin(geo_df, d_gdf)

# TWD97經緯度=WGS84 ?

county = geo_df.COUNTYNAME.unique()

for c in county:
    # print(c)
    d_list = join[join['COUNTYNAME']==c].did.unique()
    d_list_str = ",".join([str(x) for x in d_list])
    num_project = 0
    num_deployment = 0
    num_image = 0
    num_working_hour = 0
    identified = 0
    species_str = ''
    sa_str = ''
    if len(d_list):
        query = f"SELECT DISTINCT(studyarea_id) FROM taicat_image WHERE deployment_id IN ({d_list_str})"
        with connection.cursor() as cursor:
            cursor.execute(query)
            sa = cursor.fetchall()
            sa = [str(s[0]) for s in sa]
            sa_str = ','.join(sa)
        query = f"""SELECT COUNT(DISTINCT(image_uuid)) FROM taicat_image WHERE species IS NOT NULL and species != '' and deployment_id IN ({d_list_str}) ;"""
        with connection.cursor() as cursor:
            cursor.execute(query)
            identified = cursor.fetchall()
        query = f"""
                SELECT COUNT(DISTINCT(d.project_id)), SUM(ds.count_working_hour)
                FROM taicat_deployment d 
                LEFT JOIN taicat_deploymentstat ds ON d.id = ds.deployment_id
                WHERE d.id IN ({d_list_str});
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            stat = cursor.fetchall()
        query = f"""
                SELECT COUNT(DISTINCT(image_uuid)) 
                FROM taicat_image 
                WHERE deployment_id IN ({d_list_str});
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            num_image = cursor.fetchall()
        query = f"""SELECT DISTINCT(species) FROM taicat_image WHERE deployment_id IN ({d_list_str})"""
        with connection.cursor() as cursor:
            cursor.execute(query)
            species = cursor.fetchall()
            species = [s[0] for s in species if s[0] in species_list]
            species_str = ','.join(species)        
        num_project = stat[0][0]
        num_deployment = len(d_list)
        num_image = num_image[0][0]
        num_working_hour = stat[0][1] if stat[0][1] else 0
        if num_image == 0:
            identified = 0
        else:
            identified = round((identified[0][0] / num_image) * 100, 2)
    # else:
    #     # 沒有該縣市的資料，填0
    #     num_project = 0
    #     num_deployment = 0
    #     num_image = 0
    #     num_working_hour = 0
    #     identified = 0
    #     species_str = ''
    # 沒有的話新增
    # 有的話更新
    if GeoStat.objects.filter(county=c).exists():
        GeoStat.objects.filter(county=c).update(
            num_project = num_project,
            num_deployment = num_deployment,
            num_image = num_image,
            num_working_hour = num_working_hour,
            identified = identified,
            species = species_str,
            studyarea = sa_str,
            last_updated = now
        )
    else:
        GeoStat.objects.create(
            county = c,
            num_project = num_project,
            num_deployment = num_deployment,
            num_image = num_image,
            num_working_hour = num_working_hour,
            identified = identified,
            species = species_str,
            studyarea = sa_str
        )
    

# center of studyarea
# 
query = f"""
    SELECT d.longitude, d.latitude, d.id, d.study_area_id, d.geodetic_datum FROM taicat_deployment d;"""
with connection.cursor() as cursor:
    cursor.execute(query)
    sa_df = cursor.fetchall()
    sa_df = pd.DataFrame(sa_df, columns=['longitude', 'latitude', 'did', 'said','geodetic_datum'])
# d_df = pd.DataFrame(Deployment.objects.all().values('longitude','latitude','id', 'geodetic_datum'))
sa_gdf = gpd.GeoDataFrame(sa_df,geometry=gpd.points_from_xy(sa_df.longitude,sa_df.latitude))
# for i in sa_gdf.index():
#     s = sa_gdf.iloc[i]
#     if s.geodetic_datum == 'TWD97':
sa_list = sa_df.said.unique()
for i in sa_list:
    # print(i)
    # print(i, sa_gdf[sa_gdf['said']==i].dissolve().centroid)
    tmp = sa_gdf[sa_gdf['said']==i]

    if tmp.empty: # moogoo: no said?, 230726
        continue

    if tmp.geodetic_datum.values[0] == 'TWD97':
        tmp = tmp.set_crs(epsg=3826, inplace=True)
        tmp = tmp.to_crs(epsg=4326)
    long = tmp[tmp['said']==i].dissolve().centroid.x[0]
    lat = tmp[tmp['said']==i].dissolve().centroid.y[0]
    if StudyAreaStat.objects.filter(studyarea_id=i).exists():
        StudyAreaStat.objects.filter(studyarea_id=i).update(
            longitude = long,
            latitude = lat,
            last_updated = timezone.now()
        )
    else:
        StudyAreaStat.objects.create(
            studyarea_id = i,
            longitude = long,
            latitude = lat,
        )

