#!/bin/bash

pushd "$(dirname $0)"
./run_command.sh ./manage.py pass_turn $1
popd
