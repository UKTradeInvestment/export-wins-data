#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

START_DATE=$(python manage.py last_import_date)
python manage.py import_and_transform_metadata && python manage.py import_api --startdate ${START_DATE:-2017-11-17T15:36:39Z} && python manage.py transform_api
