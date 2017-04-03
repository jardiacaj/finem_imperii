#!/bin/bash

set -e

pushd $(dirname $0)/..
./manage.py migrate
./manage.py loaddata world1 simple_world
popd
