from unittest.mock import patch, NonCallableMock

from django.test import TestCase

from spi.views import get_sock_names, ValidatedUser
from spi.spi_utils import CacheableSpiCase, SpiUserInfo
from wiki_interface import Wiki


# pylint: disable=invalid-name


class GetSockNamesTest(TestCase):
    def setUp(self):
        # In theory, we've patched Wiki so this should be a no-op.
        # It's just here to catch anyplace where we might have missed
        # patching something and should prevent any actual network
        # traffic from leaking.
        site_patcher = patch('wiki_interface.wiki.Site', autospec=True)
        MockSiteClass = site_patcher.start()
        MockSiteClass.side_effect = RuntimeError
        self.addCleanup(site_patcher.stop)


    @patch('spi.views.CacheableSpiCase')
    @patch('spi.views.cache')
    def test_get_sock_names_returns_empty_list_for_empty_case(self, cache, mock_CacheableSpiCase):
        cache.get.return_value = None
        mock_CacheableSpiCase.get.return_value = CacheableSpiCase('fred', 1, [], [])
        wiki = NonCallableMock(Wiki)
        wiki.valid_usernames.return_value = set()
        sock_names = get_sock_names(wiki, 'fred')
        self.assertEqual(sock_names, [])


    @patch('spi.views.CacheableSpiCase')
    @patch('spi.views.cache')
    def test_get_sock_names_returns_valid_names_for_case(self, cache, mock_CacheableSpiCase):
        cache.get.return_value = None
        mock_CacheableSpiCase.get.return_value = CacheableSpiCase('fred',
                                                                  1,
                                                                  [SpiUserInfo('sock1', '1 January 2020'),
                                                                   SpiUserInfo('sock2', '1 January 2020'),
                                                                   SpiUserInfo('1.2.3.4', '1 January 2020'),
                                                                   SpiUserInfo('1.2.3.0/24', '1 January 2020')],
                                                                  [])
        wiki = NonCallableMock(Wiki)
        wiki.valid_usernames.return_value = set(['sock1', 'sock2', '1.2.3.4'])
        socks = get_sock_names(wiki, 'fred')
        wiki.valid_usernames.assert_called_once_with(['sock1', 'sock2', '1.2.3.4', '1.2.3.0/24'])
        self.assertCountEqual(socks, [ValidatedUser('sock1', '1 January 2020', True),
                                      ValidatedUser('sock2', '1 January 2020', True),
                                      ValidatedUser('1.2.3.4', '1 January 2020', True),
                                      ValidatedUser('1.2.3.0/24', '1 January 2020', False)])
