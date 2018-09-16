#!/bin/bash

set -e

pushd "$(dirname $0)/.."
source venv/bin/activate
python3 ./manage.py migrate
python3 ./manage.py loaddata world1 simple_world
python3 ./manage.py initialize_world 1 2
popd
