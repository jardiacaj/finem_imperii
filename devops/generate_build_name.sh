#!/bin/ash

GIT_REV=$(git rev-parse HEAD | cut -c -7)
echo "build = '$GIT_REV'" > finem_imperii/bulid.py
echo "$GIT_REV" > base/templates/base/build.html
