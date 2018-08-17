#!/bin/ash

set -e

cd /var/www/finem_imperii
# wget http://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64
# chmod +x test-reporter-latest-linux-amd64
# ./test-reporter-latest-linux-amd64 before-build
pip3 install coveralls
apk add --no-cache git
coverage run --branch --source . ./manage.py test

if [ -z "$COVERALLS_REPO_TOKEN" ]; then
    echo "Not running coveralls reporter (token missing)"
else
    coveralls
fi

#if [ -z "$CC_TEST_REPORTER_ID" ]; then
#    echo "Not running codeclimate reporter (token missing)"
#else
#    coverage xml
#    ./test-reporter-latest-linux-amd64 after-build --coverage-input-type coverage.py || true
#fi
