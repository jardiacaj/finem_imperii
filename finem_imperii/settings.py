import sys

from finem_imperii.settings_common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'de9z32-e)!-2!!*5iw7uqh*uk-f9#ivxhb3f4p-l)8qg)nsxyg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '/var/run/mysqld/mysqld.sock',
            'NAME': 'fi',
            'PASSWORD': 'fi',
            'USER': 'fi',
            'OPTIONS': {"init_command": "SET storage_engine=INNODB"}
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '/var/run/mysqld/mysqld.sock',
            'NAME': 'fi',
            'PASSWORD': 'fi',
            'USER': 'fi',
            'OPTIONS': {"init_command": "SET storage_engine=INNODB"}
        }
    }
