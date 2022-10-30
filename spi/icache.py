"""An instrumented wrapper around the standard django cache.

"""

import logging
import time
from django.core.cache import cache as django_cache
from django_tools.middlewares import ThreadLocal


logger = logging.getLogger('spi.icache')


def _use_cache():
    request = ThreadLocal.get_current_request()
    if request:
        return int(request.GET.get('use_cache', '1'))
    else:
        # This branch is only expected to be executed in a test
        # environment.  Having this here avoids the need to patch
        # zillions of existing unit tests.
        return 1


def set(key, value, *args, **kwargs):
    if _use_cache():
        t0 = time.time()
        django_cache.set(key, value, *args, **kwargs)
        dt = time.time() - t0
        logger.info("icache.set(%s) took %.3f sec", key, dt)
    else:
        logger.info("icache.set(%s) bypassed", key)


def get(key, *args, **kwargs):
    if _use_cache():
        t0 = time.time()
        data = django_cache.get(key, *args, **kwargs)
        dt = time.time() - t0
        logger.info("icache.get(%s) took %.3f sec", key, dt)
        return data
    else:
        logger.info("icache.get(%s) bypassed", key)
        return None


def get_or_set(key, default, *args, **kwargs):
    if _use_cache():
        t0 = time.time()
        data = django_cache.get_or_set(key, default, *args, **kwargs)
        dt = time.time() - t0
        logger.info("icache.get_or_set(%s) took %.3f sec", key, dt)
        return data
    else:
        logger.info("icache.get_or_set(%s) bypassed", key)
        return None
