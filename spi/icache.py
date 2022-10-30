"""An instrumented wrapper around the standard django cache.

"""

import logging
from logging import INFO, WARNING
import time
from django.core.cache import cache as django_cache
from django_tools.middlewares import ThreadLocal


logger = logging.getLogger('spi.icache')


def _use_cache():
    request = ThreadLocal.get_current_request()
    if request:
        return int(request.GET.get('use-cache', '1'))
    else:
        # This branch is only expected to be executed in a test
        # environment.  Having this here avoids the need to patch
        # zillions of existing unit tests.
        return 1


def set(key, value, *args, **kwargs):
    if _use_cache():
        t0 = time.time()
        logger.debug("calling set(%s)", key)
        django_cache.set(key, value, *args, **kwargs)
        dt = time.time() - t0
        logger.log(WARNING if dt > 0.1 else INFO, "set(%s) took %.3f sec", key, dt)
    else:
        logger.info("set(%s) bypassed", key)


def get(key, *args, **kwargs):
    if _use_cache():
        t0 = time.time()
        logger.debug("calling get(%s)", key)
        data = django_cache.get(key, *args, **kwargs)
        dt = time.time() - t0
        logger.log(WARNING if dt > 0.1 else INFO, "get(%s) took %.3f sec", key, dt)
        return data
    else:
        logger.info("get(%s) bypassed", key)
        return None


def get_or_set(key, default, *args, **kwargs):
    if _use_cache():
        t0 = time.time()
        logger.debug("calling get_or_set(%s)", key)
        data = django_cache.get_or_set(key, default, *args, **kwargs)
        dt = time.time() - t0
        logger.log(WARNING if dt > 0.1 else INFO, "get_or_set(%s) took %.3f sec", key, dt)
        return data
    else:
        logger.info("get_or_set(%s) bypassed", key)
        return None
