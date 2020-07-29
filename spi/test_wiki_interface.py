from unittest import TestCase
from unittest.mock import patch

from django.conf import settings

from .wiki_interface import Wiki


class WikiTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    @patch('django.contrib.auth.get_user')
    def test_construct_anonymous(self, mock_get_user, mock_Site):
        mock_get_user().is_anonymous = True

        Wiki(None)

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(kwargs, {'clients_useragent': settings.MEDIAWIKI_USER_AGENT})

    @patch('spi.wiki_interface.Site')
    @patch('django.contrib.auth.get_user')
    def test_construct_authenticated(self, mock_get_user, mock_Site):
        mock_get_user().is_anonymous = False

        Wiki(None)

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(set(kwargs.keys()), {'clients_useragent',
                                              'consumer_token',
                                              'consumer_secret',
                                              'access_token',
                                              'access_secret'})
        self.assertEqual(kwargs['clients_useragent'], settings.MEDIAWIKI_USER_AGENT)
