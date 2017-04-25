# HOW-TO: Server set up

To set up a server, there are different options:

|Option | Good for | Bad for | Notes
|------ |--------- |-------- | -----
|Djago development server | development | production |
|Docker | production, test running | | fastest to set up
|Manual set up | | | most complex to set and maintain


## Docker

 - Ensure that you have [installed docker][2].
 - Start the public image `jardiacaj/finem_imperii` while exposing
 port 80. You may do this with the following command:
 `sudo docker run -d -p 80:80 jardiacaj/finem_imperii`.

You should now be able to access the Finem Imperii server at
http://localhost/.


## Django development server

This guide assumes a GNU/Linux environment. Installation on different
OSes should be similar.

 - Ensure you have Python 3 and pip installed. Finem imperii has been
 tested with versions 3.4 to 3.6. The required packages are commonly
 named `python3` and `python3-pip`.
 - Go to the directory where you downloaded the Finem Imperii code.
 - Run `sudo pip3 install -r requirements.txt` to install the required
 python dependencies.
 - Run `devops/db_recreate.sh` to initialize the database. You will be
 asked the password for the admin user.
 - Run `python3 manage.py runserver` to start the development server.

You should now be able to access your Django development server at
http://localhost:8000/.

For more information on the Django development server, refer to
[its documentation][1].

[1]: https://docs.djangoproject.com/en/1.11/ref/django-admin/#django-admin-runserver
[2]: https://docs.docker.com/engine/installation/
