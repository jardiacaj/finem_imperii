#!/bin/bash

pushd "$(dirname $0)"
docker run \
  --rm \
  -v fi:/var/www/finem_imperii/prod \
  -v fi_logs:/var/logs -d jardiacaj/finem_imperii \
  -v backups:/var/www/finem_imperii/backups \
  -e DJANGO_SETTINGS_MODULE=prod.settings \
  bin/bash \
  `./manage.py dumpdata | gzip > "backups/$(date --iso-8601=seconds).gz"`
popd
