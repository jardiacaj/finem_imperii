#!/bin/sh

rm -i finem_imperii/db.sqlite3

set -e

$(dirname $0)/db_create.sh

echo "Creating superuser..."
finem_imperii/manage.py createsuperuser --username admin --email noreply@joanardiaca.net

