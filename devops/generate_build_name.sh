#!/bin/ash

git rev-parse HEAD | cut -c -7 > base/templates/base/build.html
echo -n " " >> base/templates/base/build.html
git tag -l --points-at HEAD >> base/templates/base/build.html
