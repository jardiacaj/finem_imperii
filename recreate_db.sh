#!/bin/bash

rm -i finem_imperii/db.sqlite3

set -e

finem_imperii/manage.py migrate
finem_imperii/manage.py loaddata world1

echo "Creating superuser..."
finem_imperii/manage.py createsuperuser --username admin --email noreply@joanardiaca.net

