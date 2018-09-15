import os

from multiprocessing.pool import Pool

import sys
from django import db
from django.db import connection


def parallel(operator, elements):
    if connection.vendor == 'sqlite' or 'test' in sys.argv:
        for element in elements:
            operator(element)
    else:
        db.connections.close_all()
        p = Pool()
        p.map(
            operator,
            elements
        )
