#!/bin/bash

set -e

pushd $(dirname $0)/..
./manage.py graph_models battle > models.dot
dot -Tpng models.dot > models.png
rm models.dot
viewnior models.png
rm models.png
popd
