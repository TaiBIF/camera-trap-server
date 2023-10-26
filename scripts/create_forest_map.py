
import geopandas as gpd
import os

geo_df = gpd.read_file('/Users/taibif/Documents/GitHub/ct22-volumes/static/map/forest_map.json')

c = geo_df.dissolve(by=['DIST_C', 'WKNG_C'], as_index=False)

c = c[['DIST_C', 'WKNG_C', 'geometry']]

c = c.to_crs(4326) # WGS84

c.to_file('./static/map/forest_map.json', driver="GeoJSON")  