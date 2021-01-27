from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import call, patch, Mock

from dateutil.parser import isoparse
from django.conf import settings
from django.http import HttpRequest
import mwclient.util
import mwclient.errors

from wiki_interface.data import WikiContrib, LogEvent
from wiki_interface.wiki import Wiki, Page
from wiki_interface.block_utils import BlockEvent, UnblockEvent


class ConstructorTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.Site')
    def test_default(self, mock_Site):
        Wiki()

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(kwargs, {'clients_useragent': settings.MEDIAWIKI_USER_AGENT})


    @patch('wiki_interface.wiki.Site')
    @patch('django.contrib.auth.get_user')
    def test_anonymous(self, mock_get_user, mock_Site):
        mock_get_user().is_anonymous = True

        Wiki(HttpRequest())

        mock_Site.assert_called_once()
        args, kwargs = mock_Site.call_args
        self.assertEqual(args, (settings.MEDIAWIKI_SITE_NAME,))
        self.assertEqual(kwargs, {'clients_useragent': settings.MEDIAWIKI_USER_AGENT})


    @patch('wiki_interface.wiki.Site')
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


class NamespaceTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.Site')
    def test_namespaces(self, mock_Site):
        mock_Site().namespaces = {0: '',
                                  1: 'Whatever'}
        wiki = Wiki()

        self.assertEqual(wiki.namespaces[0], '')
        self.assertEqual(wiki.namespaces[1], 'Whatever')
        self.assertEqual(wiki.namespace_values[''], 0)
        self.assertEqual(wiki.namespace_values['Whatever'], 1)


class WikiContribTest(TestCase):
    def test_construct_default(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'user', 0, 'title', 'comment')
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.user_name, 'user')
        self.assertEqual(contrib.title, 'title')
        self.assertEqual(contrib.comment, 'comment')
        self.assertTrue(contrib.is_live)


    def test_construct_live_true(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'user', 0, 'title', 'comment', is_live=True)
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.user_name, 'user')
        self.assertEqual(contrib.title, 'title')
        self.assertEqual(contrib.comment, 'comment')
        self.assertTrue(contrib.is_live)


    def test_construct_live_false(self):
        contrib = WikiContrib(datetime(2020, 7, 30), 'user', 0, 'title', 'comment', is_live=False)
        self.assertEqual(contrib.timestamp, datetime(2020, 7, 30))
        self.assertEqual(contrib.user_name, 'user')
        self.assertEqual(contrib.title, 'title')
        self.assertEqual(contrib.comment, 'comment')
        self.assertFalse(contrib.is_live)


class UserContributionsTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.Site')
    def test_user_contributions_with_string(self, mock_Site):
        mock_Site().usercontributions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
             'ns': 0, 'user': 'fred', 'title': 'p1', 'comment': 'c1'},
            {'timestamp': (2020, 7, 29, 0, 0, 0, 0, 0, 0),
             'ns': 0, 'user': 'fred', 'title': 'p2', 'comment': 'c2'}]
        wiki = Wiki()

        contributions = list(wiki.user_contributions('fred'))

        mock_Site().usercontributions.assert_called_once_with('fred',
                                                              prop='title|timestamp|comment|flags',
                                                              show='')
        self.assertIsInstance(contributions[0], WikiContrib)
        self.assertEqual(contributions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'fred', 0, 'p1', 'c1'),
            WikiContrib(datetime(2020, 7, 29, tzinfo=timezone.utc), 'fred', 0, 'p2', 'c2')])


    @patch('wiki_interface.wiki.Site')
    def test_user_contributions_with_list_of_strings(self, mock_Site):
        mock_Site().usercontributions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
             'user': 'bob', 'ns': 0, 'title': 'p1', 'comment': 'c1'},
            {'timestamp': (2020, 7, 29, 0, 0, 0, 0, 0, 0),
             'user': 'bob', 'ns': 0, 'title': 'p2', 'comment': 'c2'},
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
             'user': 'alice', 'ns': 0, 'title': 'p3', 'comment': 'c3'}]
        wiki = Wiki()

        contributions = list(wiki.user_contributions(['bob', 'alice']))

        mock_Site().usercontributions.assert_called_once_with('bob|alice',
                                                              prop='title|timestamp|comment|flags',
                                                              show='')
        self.assertIsInstance(contributions[0], WikiContrib)
        self.assertEqual(contributions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'bob', 0, 'p1', 'c1'),
            WikiContrib(datetime(2020, 7, 29, tzinfo=timezone.utc), 'bob', 0, 'p2', 'c2'),
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'alice', 0, 'p3', 'c3')])


    @patch('wiki_interface.wiki.Site')
    def test_user_contributions_raises_value_error_with_pipe_in_name(self, mock_Site):
        mock_Site().usercontributions.return_value = iter([])
        wiki = Wiki()

        with self.assertRaises(ValueError):
            list(wiki.user_contributions('foo|bar'))


    @patch('wiki_interface.wiki.Site')
    def test_user_contributions_with_too_many_names(self, mock_Site):
        mock_Site().usercontributions.side_effect = [
            [{'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
              'user': 'bob',
              'ns': 0,
              'title': 'p1',
              'comment': 'c1'}],
            [{'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0),
              'user': 'alice',
              'ns': 0,
              'title': 'p2',
              'comment': 'c2'}],
        ]
        wiki = Wiki()

        # This is a hack.  In theory, we should paramaterize the test
        # to work with any value of MAX_UCUSER.  In practice, doing so
        # is just more effort (and complicated test code) than is
        # worth it.  At least this future-proofs us a bit.
        self.assertEqual(wiki.MAX_UCUSER, 50)

        user_names = [str(i) for i in range(55)]
        contributions = list(wiki.user_contributions(user_names))

        self.assertEqual(mock_Site().usercontributions.call_args_list,
                         [call('0|1|2|3|4|5|6|7|8|9'
                               '|10|11|12|13|14|15|16|17|18|19'
                               '|20|21|22|23|24|25|26|27|28|29'
                               '|30|31|32|33|34|35|36|37|38|39'
                               '|40|41|42|43|44|45|46|47|48|49',
                               prop='title|timestamp|comment|flags',
                               show=''),
                          call('50|51|52|53|54',
                               prop='title|timestamp|comment|flags',
                               show=''),
                         ])
        self.assertEqual(contributions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'bob', 0, 'p1', 'c1'),
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'alice', 0, 'p2', 'c2')])


class DeletedUserContributionsTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.List')
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
                        'fred', 0, 'p1', 'c1', is_live=False),
            WikiContrib(datetime(2015, 11, 24, tzinfo=timezone.utc),
                        'fred', 0, 'p1', 'c2', is_live=False)])


    @patch('wiki_interface.wiki.List')
    def test_deleted_user_contributions_with_permission_denied_exception(self, mock_List):
        mock_List().__iter__.side_effect = mwclient.errors.APIError('permissiondenied',
                                                                    'blah',
                                                                    'blah-blah')
        wiki = Wiki()

        deleted_contributions = wiki.deleted_user_contributions('fred')

        self.assertEqual(list(deleted_contributions), [])


class GetUserBlocksTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.logger')
    @patch('wiki_interface.wiki.Site')
    def test_get_user_blocks_with_no_blocks(self, mock_Site, mock_logger):
        mock_Site().logevents.return_value = iter([])
        wiki = Wiki()

        user_blocks = wiki.get_user_blocks('fred')

        self.assertEqual(user_blocks, [])
        mock_logger.error.assert_not_called()


    @patch('wiki_interface.wiki.logger')
    @patch('wiki_interface.wiki.Site')
    def test_get_user_blocks_with_multiple_events(self, mock_Site, mock_logger):
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
        mock_logger.error.assert_not_called()


    @patch('wiki_interface.wiki.logger')
    @patch('wiki_interface.wiki.Site')
    def test_get_user_blocks_with_reblock(self, mock_Site, mock_logger):
        jan_1 = '2020-01-01T00:00:00Z'
        jan_2 = '2020-01-02T00:00:00Z'
        feb_1 = '2020-02-01T00:00:00Z'
        mar_1 = '2020-03-01T00:00:00Z'

        mock_Site().logevents.return_value = iter([
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(jan_1),
             'params': {'expiry': feb_1},
             'type': 'block',
             'action': 'block'},
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(jan_2),
             'params': {'expiry': mar_1},
             'type': 'block',
             'action': 'reblock'},
        ])
        wiki = Wiki()

        user_blocks = wiki.get_user_blocks('fred')

        self.assertEqual(user_blocks, [BlockEvent('fred', isoparse(jan_1), isoparse(feb_1)),
                                       BlockEvent('fred', isoparse(jan_2), isoparse(mar_1),
                                                  is_reblock=True)])
        mock_logger.error.assert_not_called()


    @patch('wiki_interface.wiki.logger')
    @patch('wiki_interface.wiki.Site')
    def test_get_user_blocks_with_unknown_action(self, mock_Site, mock_logger):
        jan_1 = '2020-01-01T00:00:00Z'
        feb_1 = '2020-02-01T00:00:00Z'
        mar_1 = '2020-03-01T00:00:00Z'
        apr_1 = '2020-04-01T00:00:00Z'

        mock_Site().logevents.return_value = iter([
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(jan_1),
             'params': {'expiry': feb_1},
             'type': 'block',
             'action': 'wugga-wugga'},
            {'title': 'User:fred',
             'timestamp': mwclient.util.parse_timestamp(mar_1),
             'params': {'expiry': apr_1},
             'type': 'block',
             'action': 'block'},
        ])
        wiki = Wiki()

        user_blocks = wiki.get_user_blocks('fred')

        self.assertEqual(user_blocks, [BlockEvent('fred', isoparse(mar_1), isoparse(apr_1))])
        mock_logger.error.assert_called_once()


class GetUserLogsTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.Site')
    def test_get_user_log_events(self, mock_Site):
        mock_Site().logevents.return_value = iter([
            {
                'title': 'Fred-sock',
                'params': {'userid': 37950265},
                'type': 'newusers',
                'action': 'create2',
                'user': 'Fred',
                'timestamp': (2019, 11, 29, 0, 0, 0, 0, 0, 0),
                'comment': 'testing',
            }
        ])
        wiki = Wiki()

        log_events = list(wiki.get_user_log_events('Fred'))
        self.assertEqual(log_events, [LogEvent(
            datetime(2019, 11, 29, tzinfo=timezone.utc),
            'Fred',
            'Fred-sock',
            'newusers',
            'create2',
            'testing')])


class GetPageTest(TestCase):
    #pylint: disable=invalid-name

    def test_page(self):
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


    @patch('wiki_interface.wiki.Site')
    def test_exists_true(self, mock_Site):
        mock_Site().pages.__getitem__().exists = True
        wiki = Wiki()
        page = Page(wiki, "my page")

        self.assertTrue(page.exists())


    @patch('wiki_interface.wiki.Site')
    def test_exists_false(self, mock_Site):
        mock_Site().pages.__getitem__().exists = False
        wiki = Wiki()
        page = Page(wiki, "my page")

        self.assertFalse(page.exists())


    @patch('wiki_interface.wiki.Site')
    def test_revisions(self, mock_Site):
        mock_Site().pages.__getitem__().revisions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0), 'user': 'fred', 'comment': 'c1'},
            {'timestamp': (2020, 7, 29, 0, 0, 0, 0, 0, 0), 'user': 'fred', 'comment': 'c2'}]
        mock_Site().pages.__getitem__().name = 'blah'
        mock_Site().pages.__getitem__().namespace = 0
        wiki = Wiki()

        revisions = list(wiki.page('blah').revisions())

        self.assertIsInstance(revisions[0], WikiContrib)
        self.assertEqual(revisions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'fred', 0, 'blah', 'c1'),
            WikiContrib(datetime(2020, 7, 29, tzinfo=timezone.utc), 'fred', 0, 'blah', 'c2')])


    @patch('wiki_interface.wiki.Site')
    def test_revisions_with_hidden_comment(self, mock_Site):
        mock_Site().pages.__getitem__().revisions.return_value = [
            {'timestamp': (2020, 7, 30, 0, 0, 0, 0, 0, 0), 'user': 'fred', 'commenthidden': ''}]
        mock_Site().pages.__getitem__().name = 'blah'
        mock_Site().pages.__getitem__().namespace = 0
        wiki = Wiki()

        revisions = list(wiki.page('blah').revisions())

        self.assertIsInstance(revisions[0], WikiContrib)
        self.assertEqual(revisions, [
            WikiContrib(datetime(2020, 7, 30, tzinfo=timezone.utc), 'fred', 0, 'blah', None)
        ])


class IsValidUsernameTest(TestCase):
    #pylint: disable=invalid-name

    @patch('wiki_interface.wiki.Site')
    def test_with_valid_name(self, mock_Site):
        mock_Site().usercontributions.return_value = []
        wiki = Wiki()

        self.assertTrue(wiki.is_valid_username('foo'))
        mock_Site().usercontributions.assert_called_once_with('foo', limit=1)


    @patch('wiki_interface.wiki.Site')
    def test_with_invalid_name(self, mock_Site):
        mock_Site().usercontributions.side_effect = mwclient.errors.APIError('baduser',
                                                                             'blah',
                                                                             None)
        wiki = Wiki()

        self.assertFalse(wiki.is_valid_username('foo'))
        mock_Site().usercontributions.assert_called_once_with('foo', limit=1)


    @patch('wiki_interface.wiki.Site')
    def test_with_unexpected_exception(self, mock_Site):
        mock_Site().usercontributions.side_effect = RuntimeError('blah')
        wiki = Wiki()

        with self.assertRaises(RuntimeError):
            wiki.is_valid_username('foo')
        mock_Site().usercontributions.assert_called_once_with('foo', limit=1)
