#!/bin/bash

set -e

pushd "$(dirname $0)/.."
venv/bin/python3 ./manage.py graph_models -a > models.dot
dot -Tpng models.dot > models.png
rm models.dot
viewnior models.png
rm models.png
popd
