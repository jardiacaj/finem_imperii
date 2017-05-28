#!/bin/ash
tail -F /var/log/apache2/access.log /var/log/apache2/error.log /var/log/django.log &
httpd -f /etc/apache2/httpd.conf -e info -DFOREGROUND
