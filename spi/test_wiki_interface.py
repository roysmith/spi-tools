import textwrap
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch, Mock

from dateutil.parser import isoparse
from django.conf import settings
from django.http import HttpRequest
import mwclient.util
import mwclient.errors

from .wiki_interface import Wiki, WikiContrib, Page
from .spi_utils import SpiIpInfo, SpiCase
from .block_utils import BlockEvent, UnblockEvent


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
        contrib = WikiContrib(datetime(2020, 7, 30), 'user', 'title', 'comment')
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.user_name, 'user')
        self.assertEqual(contrib.title, 'title')
        self.assertEqual(contrib.comment, 'comment')
        self.assertTrue(contrib.is_live)


    def test_construct_live_true(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'user', 'title', 'comment', is_live=True)
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.user_name, 'user')
        self.assertEqual(contrib.title, 'title')
        self.assertEqual(contrib.comment, 'comment')
        self.assertTrue(contrib.is_live)


    def test_construct_live_false(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'user', 'title', 'comment', is_live=False)
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.user_name, 'user')
        self.assertEqual(contrib.title, 'title')
        self.assertEqual(contrib.comment, 'comment')
        self.assertFalse(contrib.is_live)


class UserContributionsTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_user_contributions_with_string(self, mock_Site):
        mock_Site().usercontributions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
             'user': 'fred', 'title': 'p1', 'comment': 'c1'},
            {'timestamp': (2020, 7, 29, 0, 0, 0, 0, 0, 0),
             'user': 'fred', 'title': 'p2', 'comment': 'c2'}]
        wiki = Wiki()

        contributions = list(wiki.user_contributions('fred'))

        mock_Site().usercontributions.assert_called_once_with('fred', show='')
        self.assertIsInstance(contributions[0], WikiContrib)
        self.assertEqual(contributions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'fred', 'p1', 'c1'),
            WikiContrib(datetime(2020, 7, 29, tzinfo=timezone.utc), 'fred', 'p2', 'c2')])


    @patch('spi.wiki_interface.Site')
    def test_user_contributions_with_list_of_strings(self, mock_Site):
        mock_Site().usercontributions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
             'user': 'bob', 'title': 'p1', 'comment': 'c1'},
            {'timestamp': (2020, 7, 29, 0, 0, 0, 0, 0, 0),
             'user': 'bob', 'title': 'p2', 'comment': 'c2'},
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
             'user': 'alice', 'title': 'p3', 'comment': 'c3'}]
        wiki = Wiki()

        contributions = list(wiki.user_contributions(['bob', 'alice']))

        mock_Site().usercontributions.assert_called_once_with('bob|alice', show='')
        self.assertIsInstance(contributions[0], WikiContrib)
        self.assertEqual(contributions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'bob', 'p1', 'c1'),
            WikiContrib(datetime(2020, 7, 29, tzinfo=timezone.utc), 'bob', 'p2', 'c2'),
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'alice', 'p3', 'c3')])


    @patch('spi.wiki_interface.Site')
    def test_user_contributions_raises_value_error_with_pipe_in_name(self, mock_Site):
        mock_Site().usercontributions.return_value = iter([])
        wiki = Wiki()

        with self.assertRaises(ValueError):
            list(wiki.user_contributions('foo|bar'))


class DeletedUserContributionsTest(TestCase):
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
            WikiContrib(datetime(2015, 11, 25, tzinfo=timezone.utc),
                        'fred', 'p1', 'c1', is_live=False),
            WikiContrib(datetime(2015, 11, 24, tzinfo=timezone.utc),
                        'fred', 'p1', 'c2', is_live=False)])


    @patch('spi.wiki_interface.List')
    def test_deleted_user_contributions_with_permission_denied_exception(self, mock_List):
        mock_List().__iter__.side_effect = mwclient.errors.APIError('permissiondenied',
                                                                    'blah',
                                                                    'blah-blah')
        wiki = Wiki()

        deleted_contributions = wiki.deleted_user_contributions('fred')

        self.assertEqual(list(deleted_contributions), [])


class GetUserBlocksTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_get_user_blocks_with_no_blocks(self, mock_Site):
        mock_Site().logevents.return_value = iter([])
        wiki = Wiki()

        user_blocks = wiki.get_user_blocks('fred')

        self.assertEqual(user_blocks, [])



    @patch('spi.wiki_interface.Site')
    def test_get_user_blocks_with_multiple_events(self, mock_Site):
        jan_1 = '2020-01-01T00:00:00Z'
        feb_1 = '2020-02-01T00:00:00Z'
        mar_1 = '2020-03-01T00:00:00Z'
        apr_1 = '2020-04-01T00:00:00Z'
        may_1 = '2020-05-01T00:00:00Z'

        mock_Site().logevents.return_value = iter([
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(jan_1),
             'params': {'expiry': feb_1},
             'type': 'block',
             'action': 'block'},
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(mar_1),
             'params': {'expiry': apr_1},
             'type': 'block',
             'action': 'block'},
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(may_1),
             'params': {},
             'type': 'block',
             'action': 'unblock'}
            ])

        wiki = Wiki()

        user_blocks = wiki.get_user_blocks('fred')

        self.assertEqual(user_blocks, [BlockEvent('fred', isoparse(jan_1), isoparse(feb_1)),
                                       BlockEvent('fred', isoparse(mar_1), isoparse(apr_1)),
                                       UnblockEvent('fred', isoparse(may_1))])


class GetPageTest(TestCase):
    #pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_page(self, mock_Site):
        wiki = Wiki()
        page = wiki.page('foo')

        self.assertIsInstance(page, Page)


class PageTest(TestCase):
    #pylint: disable=invalid-name

    def test_construct(self):
        wiki = Wiki()
        page = Page(wiki, "my page")

        self.assertEqual(page.wiki, wiki)
        self.assertIsNotNone(page.mw_page)


    @patch('spi.wiki_interface.Site')
    def test_exists_true(self, mock_Site):
        mock_Site().pages.__getitem__().exists = True
        wiki = Wiki()
        page = Page(wiki, "my page")

        self.assertTrue(page.exists())


    @patch('spi.wiki_interface.Site')
    def test_exists_false(self, mock_Site):
        mock_Site().pages.__getitem__().exists = False
        wiki = Wiki()
        page = Page(wiki, "my page")

        self.assertFalse(page.exists())
