FROM alpine:3.5
MAINTAINER "Joan Ardiaca Jové"

# Base packages
RUN apk add --update --no-cache apache2 python3 bash git mariadb-dev gcc \
  python3-dev coreutils expect gettext mariadb-dev libffi-dev
RUN apk add --virtual build-dependence pkgconfig g++ tzdata

RUN ln -s /usr/bin/python3.5 /usr/bin/python

# Code
RUN mkdir /var/www/finem_imperii
WORKDIR /var/www/finem_imperii
ADD . .
RUN pip3 install -r requirements.txt
RUN mkdir /var/www/finem_imperii/prod

# Application
RUN rm db.sqlite3 || true
RUN devops/db_create.sh
RUN python3 ./manage.py collectstatic --no-input
RUN chown apache db.sqlite3 . /var/log
RUN devops/generate_build_name.sh

# Apache
RUN rm /etc/apache2/conf.d/languages.conf /etc/apache2/conf.d/userdir.conf /etc/apache2/conf.d/info.conf
RUN cp devops/mod_wsgi.conf devops/finem_imperii_vhost.conf /etc/apache2/conf.d
RUN cp devops/mod_wsgi.so /usr/lib/apache2/mod_wsgi.so
RUN mkdir /run/apache2

CMD devops/alpine_entry.sh
