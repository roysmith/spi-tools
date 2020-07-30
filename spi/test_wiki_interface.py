import textwrap
from unittest import TestCase
from unittest.mock import patch, Mock

from django.conf import settings
from django.http import HttpRequest

from .wiki_interface import Wiki
from .spi_utils import SpiIpInfo


class ConstructorTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_default(self, mock_Site):
        Wiki()

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(kwargs, {'clients_useragent': settings.MEDIAWIKI_USER_AGENT})


    @patch('spi.wiki_interface.Site')
    @patch('django.contrib.auth.get_user')
    def test_anonymous(self, mock_get_user, mock_Site):
        mock_get_user().is_anonymous = True

        Wiki(HttpRequest())

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(kwargs, {'clients_useragent': settings.MEDIAWIKI_USER_AGENT})


    @patch('spi.wiki_interface.Site')
    @patch('django.contrib.auth.get_user')
    def test_authenticated(self, mock_get_user, mock_Site):
        mock_get_user().is_anonymous = False

        Wiki(HttpRequest())

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(set(kwargs.keys()), {'clients_useragent',
                                              'consumer_token',
                                              'consumer_secret',
                                              'access_token',
                                              'access_secret'})
        self.assertEqual(kwargs['clients_useragent'], settings.MEDIAWIKI_USER_AGENT)


class GetCurrentCaseNamesTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_no_entries(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = ''

        wiki = Wiki()
        names = wiki.get_current_case_names()

        self.assertEqual(names, [])


    @patch('spi.wiki_interface.Site')
    def test_multiple_entries_with_duplicates(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        {{SPIstatusheader}}
        {{SPIstatusentry|Rajumitwa878|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        {{SPIstatusentry|Trumanshow69|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        '''

        wiki = Wiki()
        names = wiki.get_current_case_names()

        self.assertEqual(set(names), {'Rajumitwa878', 'AntiRacistSwede', 'Trumanshow69'})


class GetCaseIpsTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_get_case_ips_with_no_data(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        {{SPIarchive notice|Maung Ko Htet}}
        '''

        wiki = Wiki()
        infos = list(wiki.get_case_ips('foo'))

        self.assertEqual(infos, [])


    @patch('spi.wiki_interface.Site')
    def test_get_case_ips_with_unique_ips(self, mock_Site):
        def mock_page(title):
            mock = Mock()
            if 'Archive' in title:
                mock.text.return_value = ''
            else:
                mock.text.return_value = textwrap.dedent('''
                {{SPIarchive notice|Maung Ko Htet}}
                ===26 July 2020===
                * {{checkip|1=136.228.174.225}}
                * {{checkip|1=136.228.174.90}}
                * {{checkip|1=136.228.174.50}}
                ''')
            return mock
        mock_Site().pages.__getitem__.side_effect = mock_page
        wiki = Wiki()

        infos = list(wiki.get_case_ips('foo'))

        self.assertCountEqual(infos,
                              [SpiIpInfo('136.228.174.225', '26 July 2020',
                                         'Wikipedia:Sockpuppet investigations/foo'),
                               SpiIpInfo('136.228.174.90', '26 July 2020',
                                         'Wikipedia:Sockpuppet investigations/foo'),
                               SpiIpInfo('136.228.174.50', '26 July 2020',
                                         'Wikipedia:Sockpuppet investigations/foo')])


    @patch('spi.wiki_interface.Site')
    def test_get_case_ips_with_duplicate_ips_does_not_dedupliate(self, mock_Site):
        def mock_page(title):
            mock = Mock()
            if 'Archive' in title:
                mock.text.return_value = ''
            else:
                mock.text.return_value = textwrap.dedent('''
                {{SPIarchive notice|Maung Ko Htet}}
                ===26 July 2020===
                * {{checkip|1=136.228.174.225}}
                * {{checkip|1=136.228.174.225}}
                ''')
            return mock
        mock_Site().pages.__getitem__.side_effect = mock_page
        wiki = Wiki()

        infos = list(wiki.get_case_ips('foo'))


        self.assertCountEqual(infos, [SpiIpInfo('136.228.174.225', '26 July 2020',
                                                'Wikipedia:Sockpuppet investigations/foo'),
                                      SpiIpInfo('136.228.174.225', '26 July 2020',
                                                'Wikipedia:Sockpuppet investigations/foo')])
