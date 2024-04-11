from taicat.models import *
from django.db import connection
from django.utils import timezone
import pandas as pd

now = timezone.now()

# ---------- HOMEPAGE MAP ----------- #
import geopandas as gpd
from conf.settings import BASE_DIR
import os

print('start HOMEPAGE MAP', now)

species_list = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']

now = timezone.now()

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
d_df_wgs84 = d_df_wgs84.set_crs(epsg=4326, inplace=True)
d_df_wgs84 = d_df_wgs84.to_crs(epsg=3824)


merged_df = pd.concat([d_df_twd97, d_df_wgs84])
d_gdf = gpd.GeoDataFrame(merged_df, crs=3824)

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
        tmp = tmp.set_crs(epsg=3826, allow_override=True)
        tmp = tmp.to_crs(epsg=4326)
    else: 
        tmp = tmp.set_crs(epsg=4326, allow_override=True)
    tmp = tmp.to_crs(epsg=3857) # 先轉換成 map projection 才能計算 centroid
    centroid_point = tmp.dissolve().centroid
    centroid_point_wgs84 = centroid_point.to_crs(epsg=4326) # 算完 centroid 再轉回 epsg:4325 畫到地圖上
    long = centroid_point_wgs84.x[0]
    lat = centroid_point_wgs84.y[0]
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

