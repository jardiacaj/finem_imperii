#!/bin/sh

set -e

pushd $(dirname $0)/..
./manage.py graph_models -a > models.dot
dot -Tpng models.dot > models.png
rm models.dot
viewnior models.png
rm models.png
popd
