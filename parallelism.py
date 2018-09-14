import os

from django.db import connection


def max_parallelism():
    if connection.vendor == 'sqlite':
        max_parallelism = 1
    else:
        max_parallelism = os.cpu_count()
    return max_parallelism
