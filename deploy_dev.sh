#!/bin/bash -xe
set -euo pipefail
IFS=$'\n\t'

docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml build
docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml run --rm sut /app/manage.py migrate
docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml run --rm sut /app/manage.py create_mi_user --email foo@bar.com
docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml run --rm sut /app/manage.py create_missing_hvcs
docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml run --rm sut /app/manage.py generate_fake_db 50 5
docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml up -d
read -n 1 -s -r -p 'Press any key to stop the system'
docker-compose --file docker-compose.yml --file docker-compose.override.dev.yml down
