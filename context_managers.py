from contextlib import contextmanager

import time

import logging


@contextmanager
def perf_timer(name):
    start_time = time.time()
    logging.info('[{}] ...'.format(name))
    yield
    elapsed = time.time() - start_time
    logging.info('[{}] in {} ms'.format(name, int(elapsed * 1000)))
