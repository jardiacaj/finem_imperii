#!/bin/ash

if [ "`git tag -l --points-at HEAD`" == "" ]; then
    git rev-parse HEAD | cut -c -8 > base/templates/base/build.html
else
    git tag -l --points-at HEAD > base/templates/base/build.html
fi
