#!/bin/bash

set -e

pushd "$(dirname $0)/.."
source venv/bin/activate
python3 ./manage.py graph_models battle > models.dot
dot -Tpng models.dot > models.png
rm models.dot
viewnior models.png
rm models.png
popd
