#!/bin/bash

pushd "$(dirname $0)"
docker rm -f $(cat live_container)
docker pull jardiacaj/finem_imperii
./run_container.sh
./run_command.sh python3 manage.py migrate
popd

