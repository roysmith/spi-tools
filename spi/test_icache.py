from unittest import TestCase
from unittest.mock import patch, PropertyMock

from spi import icache


@patch('spi.icache.django_cache')
@patch('spi.icache.ThreadLocal')
class IcacheTest(TestCase):
    def test_cache_is_called_with_use_cache_equals_1(self, Thread_Local, django_cache):
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={'use_cache': '1'})

        icache.set('key', 'value')
        icache.get('key')
        icache.get_or_set('key', 'default')

        django_cache.set.assert_called_once_with('key', 'value')
        django_cache.get.assert_called_once_with('key')
        django_cache.get_or_set.assert_called_once_with('key', 'default')


    def test_cache_is_called_with_use_cache_missing(self, Thread_Local, django_cache):
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={})

        icache.set('key', 'value')
        icache.get('key')
        icache.get_or_set('key', 'default')

        django_cache.set.assert_called_once_with('key', 'value')
        django_cache.get.assert_called_once_with('key')
        django_cache.get_or_set.assert_called_once_with('key', 'default')


    def test_cache_is_not_called_with_use_cache_equals_0(self, Thread_Local, django_cache):
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={'use_cache': '0'})

        icache.set('key', 'value')
        icache.get('key')
        icache.get_or_set('key', 'default')

        django_cache.set.assert_not_called()
        django_cache.get.assert_not_called()
        django_cache.get_or_set.assert_not_called()
