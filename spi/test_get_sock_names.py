from unittest.mock import patch, call, MagicMock, NonCallableMock

from django.test import TestCase

from spi.views import get_sock_names, ValidatedUser, SockType
from spi.spi_utils import CacheableSpiCase, SpiUserInfo
from wiki_interface import Wiki, Category


# pylint: disable=invalid-name


class ValidatedUserTest(TestCase):
    def test_default_sock_type_is_none(self):
        user = ValidatedUser('foo', '1 January 2020', True)
        self.assertEqual(user.sock_type, SockType.NONE)


    def test_sock_type_can_be_set(self):
        user = ValidatedUser('foo', '1 January 2020', True, SockType.KNOWN)
        self.assertEqual(user.sock_type, SockType.KNOWN)


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
        wiki.validate_usernames.return_value = {}
        wiki.category().members.return_value = []
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
        wiki.validate_usernames.return_value = {'1.2.3.0/24'}
        wiki.category().members.return_value = []
        socks = get_sock_names(wiki, 'fred')
        wiki.validate_usernames.assert_called_once_with(['sock1', 'sock2', '1.2.3.4', '1.2.3.0/24'])
        self.assertCountEqual(socks, [ValidatedUser('sock1', '1 January 2020', True),
                                      ValidatedUser('sock2', '1 January 2020', True),
                                      ValidatedUser('1.2.3.4', '1 January 2020', True),
                                      ValidatedUser('1.2.3.0/24', '1 January 2020', False)])


    @patch('spi.views.CacheableSpiCase')
    @patch('spi.views.cache')
    def test_get_sock_names_retrieves_sock_categories(self, cache, mock_CacheableSpiCase):
        cache.get.return_value = None
        mock_CacheableSpiCase.get.return_value = CacheableSpiCase('Fred',
                                                                  1,
                                                                  [SpiUserInfo('sock1', '1 January 2020'),
                                                                   SpiUserInfo('sock2', '1 January 2020'),
                                                                   SpiUserInfo('sock3', '1 January 2020')],
                                                                  [])
        wiki = NonCallableMock(Wiki)
        wiki.validate_usernames.return_value = {}
        wiki.category = MagicMock(Category)
        wiki.category.reset_mock()
        socks = get_sock_names(wiki, 'Fred')
        self.assertEqual(wiki.category.call_args_list,
                         [call('Wikipedia sockpuppets of Fred'),
                          call('Suspected Wikipedia sockpuppets of Fred')])


    @patch('spi.views.CacheableSpiCase')
    @patch('spi.views.cache')
    def test_get_sock_names_marks_sock_types(self, cache, mock_CacheableSpiCase):
        cache.get.return_value = None
        mock_CacheableSpiCase.get.return_value = CacheableSpiCase('Fred',
                                                                  1,
                                                                  [SpiUserInfo('sock1', '1 January 2020'),
                                                                   SpiUserInfo('sock2', '1 January 2020'),
                                                                   SpiUserInfo('sock3', '1 January 2020')],
                                                                  [])
        wiki = NonCallableMock(Wiki)
        wiki.validate_usernames.return_value = {}
        wiki.category = MagicMock(Category)
        wiki.category().members.side_effect = [['User:sock1'],
                                               ['User:sock2']]
        wiki.category.reset_mock()
        socks = get_sock_names(wiki, 'Fred')
        self.assertEqual(wiki.category.call_args_list,
                         [call('Wikipedia sockpuppets of Fred'),
                          call('Suspected Wikipedia sockpuppets of Fred')])
        self.assertCountEqual(list(socks),
                              [ValidatedUser('sock1', '1 January 2020', True, SockType.KNOWN),
                               ValidatedUser('sock2', '1 January 2020', True, SockType.SUSPECTED),
                               ValidatedUser('sock3', '1 January 2020', True, SockType.NONE)])
