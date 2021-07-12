from unittest import TestCase
from unittest.mock import patch, NonCallableMock
from datetime import datetime

from wiki_interface import Wiki, WikiContrib
from spi.user_utils import CacheableUserContribs


class CacheableUserContribsTest(TestCase):
    @patch('spi.user_utils.cache')
    def test_construct(self, cache):
        contribs = CacheableUserContribs()

        cache.get.assert_not_called()
        cache.set.assert_not_called()
        self.assertEqual(contribs.data, [])


    @patch('spi.user_utils.cache')
    def test_get_returns_empty_contribs_list_with_no_contribs_and_empty_cache(self, cache):
        wiki = NonCallableMock(Wiki)
        cache.get.return_value = []
        wiki.user_contributions.return_value = []

        contribs = CacheableUserContribs.get(wiki, 'Fred')

        key = 'spi.CacheableUserContribs.Fred'
        expected_contribs = CacheableUserContribs([])
        cache.get.assert_called_once_with(key, default=[])
        cache.set.assert_not_called()
        wiki.user_contributions.assert_called_once_with('Fred', end=None)
        self.assertEqual(contribs, expected_contribs)


    @patch('spi.user_utils.cache')
    def test_get_returns_correct_data_with_wiki_data_and_empty_cache(self, cache):
        wiki = NonCallableMock(Wiki)
        cache.get.return_value = []
        wiki.user_contributions.return_value = [
            WikiContrib(1000, datetime(2020, 1, 1), 'Fred', 0, 'Foo', ''),
        ]

        contribs = CacheableUserContribs.get(wiki, 'Fred')

        expected_contribs = CacheableUserContribs([WikiContrib(1000, datetime(2020, 1, 1), 'Fred', 0, 'Foo', '')])
        key = 'spi.CacheableUserContribs.Fred'
        cache.get.assert_called_once_with(key, default=[])
        cache.set.assert_called_once_with(key, expected_contribs.data)
        wiki.user_contributions.assert_called_once_with('Fred', end=None)
        self.assertEqual(contribs, expected_contribs)


    @patch('spi.user_utils.cache')
    def test_get_returns_correct_data_with_no_wiki_data_and_valid_cache(self, cache):
        wiki = NonCallableMock(Wiki)
        cache.get.return_value = [WikiContrib(2020_01_01, datetime(2020, 1, 1), 'Fred', 0, 'Foo', '')]
        wiki.user_contributions.return_value = []

        contribs = CacheableUserContribs.get(wiki, 'Fred')

        expected_contribs = CacheableUserContribs([WikiContrib(2020_01_01, datetime(2020, 1, 1), 'Fred', 0, 'Foo', '')])
        key = 'spi.CacheableUserContribs.Fred'
        cache.get.assert_called_once_with(key, default=[])
        cache.set.assert_not_called()
        wiki.user_contributions.assert_called_once_with('Fred', end='2020-01-01T00:00:00')
        self.assertEqual(contribs, expected_contribs)


    @patch('spi.user_utils.cache')
    def test_get_checks_for_contribs_newer_than_cached_data(self, cache):
        wiki = NonCallableMock(Wiki)
        cache.get.return_value = [WikiContrib(2020_01_01, datetime(2020, 1, 1), 'Fred', 0, 'Foo', '')]
        wiki.user_contributions.return_value = [WikiContrib(2020_01_02, datetime(2020, 1, 2), 'Fred', 0, 'Foo', '')]

        contribs = CacheableUserContribs.get(wiki, 'Fred')

        expected_contribs = CacheableUserContribs([
            WikiContrib(2020_01_02, datetime(2020, 1, 2), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_01, datetime(2020, 1, 1), 'Fred', 0, 'Foo', ''),
        ])
        key = 'spi.CacheableUserContribs.Fred'
        cache.get.assert_called_once_with(key, default=[])
        cache.set.assert_called_once_with(key, expected_contribs.data)
        wiki.user_contributions.assert_called_once_with('Fred', end='2020-01-01T00:00:00')
        self.assertEqual(contribs, expected_contribs)


    @patch('spi.user_utils.cache')
    def test_get_eliminates_last_new_data_item_that_duplicates_first_cached_item(self, cache):
        wiki = NonCallableMock(Wiki)
        cache.get.return_value = [
            WikiContrib(2020_01_03, datetime(2020, 1, 3), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_02, datetime(2020, 1, 2), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_01, datetime(2020, 1, 1), 'Fred', 0, 'Foo', ''),
            ]
        wiki.user_contributions.return_value = [
            WikiContrib(2020_01_05, datetime(2020, 1, 5), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_04, datetime(2020, 1, 4), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_03, datetime(2020, 1, 3), 'Fred', 0, 'Foo', ''),
            ]

        contribs = CacheableUserContribs.get(wiki, 'Fred')

        expected_contribs = CacheableUserContribs([
            WikiContrib(2020_01_05, datetime(2020, 1, 5), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_04, datetime(2020, 1, 4), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_03, datetime(2020, 1, 3), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_02, datetime(2020, 1, 2), 'Fred', 0, 'Foo', ''),
            WikiContrib(2020_01_01, datetime(2020, 1, 1), 'Fred', 0, 'Foo', ''),
            ])
        key = 'spi.CacheableUserContribs.Fred'
        cache.get.assert_called_once_with(key, default=[])
        cache.set.assert_called_once_with(key, expected_contribs.data)
        wiki.user_contributions.assert_called_once_with('Fred', end='2020-01-03T00:00:00')
        self.assertEqual(contribs, expected_contribs)
