#!/bin/bash

pushd "$(dirname $0)"
docker run -v fi:/var/www/finem_imperii/prod -v fi_logs:/var/logs -v fi_backups:/backups -p 8000:80 -d jardiacaj/finem_imperii > live_container
popd

