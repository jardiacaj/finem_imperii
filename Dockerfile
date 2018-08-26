FROM alpine:3.8
MAINTAINER "Joan Ardiaca Jové"

# Base packages
RUN apk add --update --no-cache apache2 python3 bash git mariadb-dev gcc \
  python3-dev coreutils expect gettext mariadb-dev libffi-dev openssl \
  && \
  apk add --virtual build-dependence pkgconfig g++ tzdata \
  && \
  ln -s /usr/bin/python3.5 /usr/bin/python

# Code
RUN mkdir /var/www/finem_imperii
WORKDIR /var/www/finem_imperii
ADD . .
RUN pip3 install -r requirements.txt \
  && \
  python3 -m venv venv \
  && \
  source venv/bin/activate && pip3 install -r requirements.txt \
  && \
  mkdir /var/www/finem_imperii/prod

# Application
RUN devops/db_create.sh \
  && \
  python3 ./manage.py collectstatic --no-input \
  && \
  chown apache db.sqlite3 . /var/log \
  && \
  devops/generate_build_name.sh

# Apache
RUN rm /etc/apache2/conf.d/languages.conf /etc/apache2/conf.d/userdir.conf /etc/apache2/conf.d/info.conf \
  && \
  cp devops/mod_wsgi.conf devops/finem_imperii_vhost.conf /etc/apache2/conf.d \
  && \
  cp devops/mod_wsgi.so /usr/lib/apache2/mod_wsgi.so \
  && \
  mkdir /run/apache2

RUN echo "export DJANGO_SETTINGS_MODULE=prod.settings" >> /root/.bashrc

CMD devops/alpine_entry.sh
