from unittest import TestCase
from unittest.mock import patch, Mock, PropertyMock

from spi import icache


@patch('spi.icache.django_cache')
@patch('spi.icache.ThreadLocal')
class IcacheTest(TestCase):
    def test_cache_is_called_with_use_cache_equals_1(self, Thread_Local, django_cache):
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={'use-cache': '1'})

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
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={'use-cache': '0'})

        icache.set('key', 'value')
        icache.get('key')
        icache.get_or_set('key', 'default')

        django_cache.set.assert_not_called()
        django_cache.get.assert_not_called()
        django_cache.get_or_set.assert_not_called()


    @patch('spi.icache.time')
    def test_message_is_logged_at_info_if_dt_less_than_100_ms(self, time, Thread_Local, django_cache):
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={})
        time.time.side_effect = [0.0, 0.05] * 3

        with self.assertLogs(logger='spi.icache') as cm:
            icache.set('key', 'value')
            icache.get('key')
            icache.get_or_set('key', 'value')

        self.assertEqual(len(cm.records), 3)
        for record in cm.records:
            self.assertEqual(record.levelname, 'INFO')


    @patch('spi.icache.time')
    def test_message_is_logged_at_warning_if_dt_greater_than_100_ms(self, time, Thread_Local, django_cache):
        type(Thread_Local.get_current_request()).GET = PropertyMock(return_value={})
        time.time.side_effect = [0.0, 0.2] * 3

        with self.assertLogs(logger='spi.icache') as cm:
            icache.set('key', 'value')
            icache.get('key')
            icache.get_or_set('key', 'value')

        self.assertEqual(len(cm.records), 3)
        for record in cm.records:
            self.assertEqual(record.levelname, 'WARNING')
