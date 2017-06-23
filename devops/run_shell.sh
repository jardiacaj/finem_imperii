#!/bin/bash

pushd "$(dirname $0)"
docker exec -e DJANGO_SETTINGS_MODULE=prod.settings -it $(cat live_container) bash
popd
