


```
CREATE EXTENSION postgis;
```

[直轄市、縣市界線(TWD97經緯度) | 政府資料開放平臺](https://data.gov.tw/dataset/7442)


copy COUNTY_MOI_1090820.shp copy COUNTY_MOI_1090820.dbf copy COUNTY_MOI_1090820.shx

```
shp2pgsql -I -s 4326 COUNTY_MOI_1090820.shp
```

-I: Create a GiST index on the geometry column
-s: from_srid

DATABASE_URL 的 postgres 改成 postgis

DATABASE_URL 是在 `scripts/entrypoint` 定義的，不是.env
