#!/bin/sh

python ./manage.py shell < ./cron_scripts/check_data_gap.py
