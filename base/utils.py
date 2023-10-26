from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.core.cache import cache
import time
from django.db import connection
from taicat.models import Image, StudyAreaStat
import pandas as pd
import json
from decimal import Decimal
from django.utils import timezone


class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)



import geopandas as gpd


def update_studyareastat(sa_list):
    query = """
        SELECT d.longitude, d.latitude, d.id, d.study_area_id, d.geodetic_datum FROM taicat_deployment d
        WHERE d.study_area_id = ANY(%s);"""
    with connection.cursor() as cursor:
        cursor.execute(query, (sa_list, ))
        sa_df = cursor.fetchall()
        sa_df = pd.DataFrame(sa_df, columns=['longitude', 'latitude', 'did', 'said','geodetic_datum'])
    sa_gdf = gpd.GeoDataFrame(sa_df,geometry=gpd.points_from_xy(sa_df.longitude,sa_df.latitude))
    # for i in sa_gdf.index():
    #     s = sa_gdf.iloc[i]
    #     if s.geodetic_datum == 'TWD97':
    sa_list = sa_df.said.unique()
    for i in sa_list:
        tmp = sa_gdf[sa_gdf['said']==i]
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

def get_request_site_url(request):
    url = f"{request.scheme}://{request.META['HTTP_HOST']}"
    return url
