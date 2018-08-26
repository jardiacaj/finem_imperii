#!/bin/bash

pushd "$(dirname $0)"
docker pull jardiacaj/finem_imperii
./run_backup_job.sh
docker rm -f $(cat live_container)
./run_dbmigrate.sh
./run_appserver.sh
popd
