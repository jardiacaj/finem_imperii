#!/bin/bash

pushd "$(dirname $0)"
docker logs -f $(cat live_container)
popd
