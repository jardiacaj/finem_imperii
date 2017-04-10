#!/bin/bash

set -e

pushd $(dirname $0)/..
./manage.py migrate
./manage.py loaddata world1 simple_world
./manage.py initialize_world 1 2
popd
