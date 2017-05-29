#!/bin/bash

docker run -v fi:/var/www/finem_imperii/prod -p 8000:80 -d jardiacaj/finem_imperii
