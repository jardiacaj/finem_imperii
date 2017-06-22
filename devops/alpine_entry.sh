#!/bin/bash
if [ ! -f /var/www/finem_imperii/prod/settings.py ]; then
  cp /var/www/finem_imperii/finem_imperii/settings.py /var/www/finem_imperii/prod/settings.py
fi
touch /var/log/django.log && chown apache /var/log/django.log
chown apache /backups || true
tail -F /var/log/apache2/access.log /var/log/apache2/error.log /var/log/django.log &
httpd -f /etc/apache2/httpd.conf -e info -DFOREGROUND
