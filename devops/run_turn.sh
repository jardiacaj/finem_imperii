#!/bin/bash

pushd "$(dirname $0)"
./run_command.sh ./manage.py dumpdata > "/backups/$(date --iso-8601=seconds)"
./run_command.sh ./manage.py pass_turn $1
popd
