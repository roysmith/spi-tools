from unittest import TestCase
from unittest.mock import patch

from django.conf import settings
from django.http import HttpRequest

from .wiki_interface import Wiki


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
    def test_multiple_entries(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        {{{{SPIstatusheader}}
        {{SPIstatusentry|Rajumitwa878|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        {{SPIstatusentry|Trumanshow69|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        '''

        wiki = Wiki()
        names = wiki.get_current_case_names()

        self.assertEqual(set(names), {'Rajumitwa878', 'AntiRacistSwede', 'Trumanshow69'})