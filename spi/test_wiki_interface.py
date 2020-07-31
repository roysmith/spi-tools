import textwrap
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch, Mock

from django.conf import settings
from django.http import HttpRequest

from .wiki_interface import Wiki, WikiContrib
from .spi_utils import SpiIpInfo, SpiCase


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


class GetCaseTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_get_case_with_one_checkuser(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = textwrap.dedent('''
        {{SPIarchive notice|foo}}
        ===26 July 2020===
        * {{checkuser|name in template}}
        ''')
        wiki = Wiki()

        case = wiki.get_case('page name', True)

        self.assertIsInstance(case, SpiCase)
        self.assertEqual(case.master_name(), 'page name')


class WikiContribTest(TestCase):
    def test_construct_default(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'my title', 'my comment')
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.title, 'my title')
        self.assertEqual(contrib.comment, 'my comment')
        self.assertTrue(contrib.is_live)


    def test_construct_live_true(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'my title', 'my comment', is_live=True)
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.title, 'my title')
        self.assertEqual(contrib.comment, 'my comment')
        self.assertTrue(contrib.is_live)


    def test_construct_live_false(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'my title', 'my comment', is_live=False)
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.title, 'my title')
        self.assertEqual(contrib.comment, 'my comment')
        self.assertFalse(contrib.is_live)


class UserContributioneTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_user_contributions(self, mock_Site):
        mock_Site().usercontributions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0), 'title': 'p1', 'comment': 'c1'},
            {'timestamp': (2020, 7, 29, 0, 0, 0, 0, 0, 0), 'title': 'p2', 'comment': 'c2'}]
        wiki = Wiki()

        contributions = wiki.user_contributions('fred')

        items = list(contributions)
        self.assertIsInstance(items[0], WikiContrib)
        self.assertEqual(items, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'p1', 'c1'),
            WikiContrib(datetime(2020, 7, 29, tzinfo=timezone.utc), 'p2', 'c2')])


class DeletedUserContributioneTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.List')
    def test_deleted_user_contributions(self, mock_List):
        # See https://www.mediawiki.org/wiki/API:Alldeletedrevisions#Response
        example_response = {
            "query": {
                "alldeletedrevisions": [
                    {
                        "pageid": 0,
                        "revisions": [
                            {
                                "timestamp": "2015-11-25T00:00:00Z",
                                "comment": "c1",
                            },
                            {
                                "timestamp": "2015-11-24T00:00:00Z",
                                "comment": "c2",
                            }

                        ],
                        "ns": 0,
                        "title": "p1"
                    }
                ]
            }
        }
        pages = example_response['query']['alldeletedrevisions']
        mock_List().__iter__ = Mock(return_value=iter(pages))
        wiki = Wiki()

        deleted_contributions = wiki.deleted_user_contributions('fred')
        items = list(deleted_contributions)
        self.assertIsInstance(items[0], WikiContrib)
        self.assertEqual(items, [
            WikiContrib(datetime(2015, 11, 25, tzinfo=timezone.utc), 'p1', 'c1', is_live=False),
            WikiContrib(datetime(2015, 11, 24, tzinfo=timezone.utc), 'p1', 'c2', is_live=False)])
