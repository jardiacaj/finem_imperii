#!/bin/bash

set -e

pushd $(dirname $0)/..
docker build -t wsgi-build -f Dockerfile.build_wsgi_alpine .
docker run -d wsgi-build
container_id=$(docker ps | grep wsgi-build | awk '{ print $1 }')
docker cp "$container_id:/usr/lib/python3.5/site-packages/mod_wsgi/server/mod_wsgi-py35.cpython-35m-x86_64-linux-gnu.so" devops/mod_wsgi.so
docker kill $container_id
docker rm -f $container_id
docker rmi wsgi-build
popd
