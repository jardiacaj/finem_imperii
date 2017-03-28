#!/bin/sh

set -e

finem_imperii/manage.py migrate
finem_imperii/manage.py loaddata world1

