# CameraTrap 2023

## Development

```
docker compose up
```

default config use `compose.yml` and `compose.override.yml`

開發流程:

1. fork repo from TaiBIF github to personal github account (first time)
2. debug start from `devel` branch (github default branch)
2. create new branch `git co -b fix-xxx`
3. `git commit `
4. `git merge fix-xxx`, `git checkout devel`
5. `git push origin devel`
6. create Pull requests in github & merge to TaiBIF/devel

正式站就 merge to main branch

### PostgreSQL

sync staging/production server database data:

1. Delete or backup `.//ct22-volumes/pgdata`
2. Get dump gziped sql file from server
3. put it in `initdb` folder
4. docker compose up

## Deployment

use `Dockerfile_prod`

Staging
```
docker compose -f compose.ylm -f compose.staging.yml up
```


Production
```
docker compose -f compose.ylm -f compose.prod.yml up
```

## Spec

### Data Model

- DeploymentJournal: 相機行程
- DeploymentStat: 相機位置工作時數
- `script/import-deployment-stat.py` 計算/匯入工作時數


## Nginx & Let's Encrypt for HTTPS
[Setup referece](https://pentacent.medium.com/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71)

Scripts:
- Nginx config: [nginx-django.conf](./scripts/nginx-django.conf)
- Docker config: [production.yml](./production.yml)
- Initialize let's encrypt: [init-letsencrypt.sh](./init-letsencrypt.sh)

NOTES: 
1. Open port 443 on EC2
2. Link nginx to django in docker config otherwise nginx cannot find correct upstream
3. Make sure to check if data path & docker-compose yml filename in `init-letsencrypt.sh` are correct
4. When developinglocally by docker, https (provided by nginx) will not be available, so login through ORCID will fail.

## Deployment

gunicorn should add `--limit-request-line 8190`, otherwise the search page download api may cause verbose querystring too long error
 
