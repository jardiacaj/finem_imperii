#!/bin/ash

set -e

pip3 install coveralls
pip3 install codeclimate-test-reporter
apk add --no-cache git
cd /var/www/finem_imperii
coverage run --branch --source . ./manage.py test

if [ -z "$COVERALLS_REPO_TOKEN" ]; then
    echo "Not running coveralls reporter (token missing)"
else
    coveralls
fi

if [ -z "$CODECLIMATE_REPO_TOKEN" ]; then
    echo "Not running codeclimate reporter (token missing)"
else
    codeclimate-test-reporter
fi
