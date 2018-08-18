# HOW-TO: Server set up

To set up a server, there are different options:

|Option | Good for | Bad for | Notes
|------ |--------- |-------- | -----
|Djago development server | development | production |
|Docker | production, test running | | fastest to set up
|Manual set up with apache/nginx/etc. | | | most complex to set and maintain

## Docker

- Ensure that you have [installed docker][2].
- Start the public image `jardiacaj/finem_imperii` while exposing
port 80. You may do this with the following command:
`sudo docker run -d -p 80:80 jardiacaj/finem_imperii`.

You should now be able to access the Finem Imperii server at
<http://localhost/>. You may log in with the test user
"alice" with the password "test".

## Django development server

This guide assumes a GNU/Linux environment. Installation on different
OSes should be similar.

- Ensure you have Python 3 and pip installed. Finem imperii has been
tested with versions 3.4 to 3.6. The required packages are commonly
named `python3` and `python3-pip`.
- Make sure you have mysql installed on your system
- Go to the directory where you downloaded the Finem Imperii code.
- Create a Python venv by running `python3 -m venv env`.
- Run `source venv/bin/activate` to activate the venv.
- Run `sudo pip3 install -r requirements.txt` to install the required
python dependencies.
- Run `devops/db_recreate.sh` to initialize the database. You will be
asked the password for the admin user.
- Run `python3 manage.py runserver` to start the development server.

You should now be able to access your Django development server at
<http://localhost:8000/>. You may log in with the test user
"alice" with the password "test".

You can stop the server by pressing Control-C. Remember to activate
the venv before to start the server.

For more information on the Django development server, refer to
[its documentation][1].

If you are interested on contributing to Finem Imperii you may want
to read the [contribution guide][3] of the project.

[1]: https://docs.djangoproject.com/en/1.11/ref/django-admin/#django-admin-runserver
[2]: https://docs.docker.com/engine/installation/
[3]: https://github.com/jardiacaj/finem_imperii/blob/master/CONTRIBUTING.md
