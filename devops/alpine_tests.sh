#!/bin/ash

set -e

cd /var/www/finem_imperii
apk add --no-cache git
coverage run --branch --source . ./manage.py test

if [ -z "$CODACY_PROJECT_TOKEN" ]; then
    echo "Not running codacy reporter (token missing)"
else
    coverage xml
    python-codacy-coverage -r coverage.xml
fi

