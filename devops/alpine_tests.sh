#!/bin/sh
set -e

pip3 install coveralls
apk add --no-cache git
cd /var/www/finem_imperii/finem_imperii
coverage run --branch --source . ./manage.py test
coveralls
