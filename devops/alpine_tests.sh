#!/bin/sh

set -e

pip3 install coveralls
pip3 install codeclimate-test-reporter
apk add --no-cache git
cd /var/www/finem_imperii
coverage run --branch --source . ./manage.py test
coveralls
codeclimate-test-reporter
