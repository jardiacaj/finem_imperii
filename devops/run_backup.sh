#!/bin/bash

pushd "$(dirname $0)"
mkdir backups || true
./run_command.sh ./manage.py dumpdata | gzip > "backups/$(date --iso-8601=seconds).gz"
popd
