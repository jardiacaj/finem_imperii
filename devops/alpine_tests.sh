#!/bin/sh
cd /var/www/fiinem_imperii/finem_imperii
pip3 install coveralls
coverage run --branch --source . ./manage.py test
coveralls
