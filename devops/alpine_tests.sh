#!/bin/sh
set -e

pip3 install coveralls
apk add --no-cache git
coverage run --branch --source . /var/www/finem_imperii/finem_imperii/manage.py test
coveralls
