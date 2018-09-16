#!/bin/bash

set -e

pushd "$(dirname $0)/.."
venv/bin/python ./manage.py migrate
venv/bin/python ./manage.py loaddata world1 simple_world corelia
venv/bin/python ./manage.py initialize_world 1 2 3
popd
