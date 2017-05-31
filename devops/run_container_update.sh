#!/bin/bash

pushd "$(dirname $0)"
docker pull jardiacaj/finem_imperii
docker rm -f $(cat live_container)
./run_container.sh
./run_command.sh python3 manage.py migrate
popd
