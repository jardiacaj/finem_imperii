from contextlib import contextmanager

import time


@contextmanager
def perf_timer(name):
    start_time = time.time()
    yield
    elapsed = time.time() - start_time
    print('[{}] in {} ms'.format(name, int(elapsed * 1000)))
