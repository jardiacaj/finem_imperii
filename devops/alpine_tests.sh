#!/bin/ash

set -e

cd /var/www/finem_imperii
apk add --no-cache git
coverage run --branch --source . ./manage.py test
