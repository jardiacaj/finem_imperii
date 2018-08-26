#!/bin/bash

pushd "$(dirname $0)"
docker exec -it -e DJANGO_SETTINGS_MODULE=prod.settings $(cat live_container) /bin/bash
popd
