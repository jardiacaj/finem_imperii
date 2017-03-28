FROM python:3.4-slim
MAINTAINER "Joan Ardiaca Jové"

# Base packages
RUN apt-get update
RUN apt-get -y install apache2 libapache2-mod-wsgi-py3

# Code
RUN mkdir /var/www/finem_imperii
WORKDIR /var/www/finem_imperii
ADD . .
RUN pip install -r requirements.txt

# Application
RUN ./db_create.sh
RUN finem_imperii/manage.py collectstatic --no-input

# Apache
RUN cp devops/finem_imperii_vhost.conf /etc/apache2/sites-enabled/000-default.conf

CMD apache2 -f /etc/apache2/apache2.conf -e info
