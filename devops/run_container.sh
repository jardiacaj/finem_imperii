#!/bin/bash

pushd "$(dirname $0)"
docker run -v fi:/var/www/finem_imperii/prod -v fi_logs:/var/logs -p 8000:80 -d jardiacaj/finem_imperii > live_container
popd

