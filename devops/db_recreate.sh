#!/bin/bash

set -e

pushd "$(dirname $0)/.."
[[ -f db.sqlite3 ]] && rm -i db.sqlite3 || true
venv/bin/python ./manage.py flush --no-input
devops/db_create.sh
echo "Creating superuser..."
venv/bin/python ./manage.py createsuperuser --username admin --email noreply@joanardiaca.net
popd
