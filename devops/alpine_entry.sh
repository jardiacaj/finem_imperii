#!/bin/bash
if [ ! -f /var/www/finem_imperii/prod/settings.py ]; then
  cp /var/www/finem_imperii/finem_imperii/settings.py /var/www/finem_imperii/prod/settings.py
fi
export DJANGO_SETTINGS_MODULE=prod.settings
tail -F /var/log/apache2/access.log /var/log/apache2/error.log /var/log/django.log &
httpd -f /etc/apache2/httpd.conf -e info -DFOREGROUND
