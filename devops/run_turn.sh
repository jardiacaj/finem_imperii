#!/bin/bash

pushd "$(dirname $0)"
./run_backup.sh
./run_command.sh ./manage.py pass_turn $1
popd
