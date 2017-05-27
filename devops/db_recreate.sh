#!/bin/bash

set -e

pushd "$(dirname $0)/.."
rm -i db.sqlite3 || true
devops/db_create.sh
echo "Creating superuser..."
python3 ./manage.py createsuperuser --username admin --email noreply@joanardiaca.net
popd
