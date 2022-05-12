from datetime import datetime
from unittest.mock import call, patch

from lxml import etree

from spi.timeline_view import TimelineEvent
from spi.test_spi_view import ViewTestCase
from spi.user_utils import CacheableUserContribs
from wiki_interface.block_utils import BlockEvent
from wiki_interface.data import WikiContrib, LogEvent

# pylint: disable=invalid-name

class TimelineViewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('spi.timeline_view')


    def test_event_list(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(103, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment'),
            WikiContrib(101, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment'),
        ]
        self.mock_wiki.deleted_user_contributions.return_value = [
            WikiContrib(102, datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', False)]
        self.mock_wiki.user_blocks.return_value = [
            BlockEvent('Wilma', datetime(2020, 2, 1), 1001)]
        self.mock_wiki.user_log_events.return_value = [
            LogEvent(1002, datetime(2019, 11, 29), 'Fred', 'Fred-sock', 'newusers', 'create2', 'testing')
        ]
        self.force_login()
        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 2, 1), 1001, 'Wilma', 'block', '', 'indef', '', ''),
            TimelineEvent(datetime(2020, 1, 3), 103, 'Fred', 'edit', '', 'Title', 'comment', ''),
            TimelineEvent(datetime(2020, 1, 2), 102, 'Fred', 'edit', 'deleted', 'Title', 'comment', ''),
            TimelineEvent(datetime(2020, 1, 1), 101, 'Fred', 'edit', '', 'Title', 'comment', ''),
            TimelineEvent(datetime(2019, 11, 29), 1002, 'Fred', 'newusers', 'create2', 'Fred-sock', 'testing', ''),
        ])


    def test_edit_event_includes_tags(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', is_live=True, tags=[]),
            WikiContrib(1002, datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', is_live=True, tags=['tag']),
            WikiContrib(1003, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', is_live=True, tags=['tag1', 'tag2']),
        ]
        self.force_login()
        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 1001, 'Fred', 'edit', '', 'Title', 'comment', ''),
            TimelineEvent(datetime(2020, 1, 2), 1002, 'Fred', 'edit', '', 'Title', 'comment', 'tag'),
            TimelineEvent(datetime(2020, 1, 3), 1003, 'Fred', 'edit', '', 'Title', 'comment', 'tag1, tag2'),
        ])


    def test_edit_event_includes_id(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', is_live=True, tags=[]),
        ]
        self.force_login()
        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 1001, 'Fred', 'edit', '', 'Title', 'comment', ''),
        ])


    def test_deleted_edit_event_includes_tags(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', is_live=False, tags=['tag1', 'tag2']),
        ]
        self.force_login()
        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 3), 1001, 'Fred', 'edit', 'deleted', 'Title', 'comment', 'tag1, tag2'),
        ])


    def test_html_includes_tags(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['my test tag']),
        ]
        self.force_login()
        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        tree = etree.HTML(response.content)
        extras = tree.cssselect('#events div.extra')
        self.assertEqual([e.text for e in extras], ['my test tag'])


    def test_context_includes_tag_list(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', tags=[]),
            WikiContrib(1002, datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', tags=['tag']),
            WikiContrib(1003, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['tag1', 'tag2', 'tag4']),
            WikiContrib(1004, datetime(2020, 1, 4), 'Wilma', 0, 'Title', 'comment', tags=['tag1', 'tag3']),
            WikiContrib(1005, datetime(2020, 1, 5), 'Barney', 0, 'Title', 'comment', tags=['tag1', 'tag2']),
        ]
        self.force_login()

        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.templates, ['spi/timeline.html'])
        self.assertEqual(response.context['tag_list'], ['tag', 'tag1', 'tag2', 'tag3', 'tag4'])


    @patch('spi.timeline_view.CacheableUserContribs', spec=CacheableUserContribs)
    def test_context_includes_tag_table(self, mock_CacheableUserContribs):
        mock_CacheableUserContribs.get.side_effect = [
            CacheableUserContribs([
                WikiContrib(1001, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', tags=[]),
                WikiContrib(1002, datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', tags=['tag1', 'tag2', 'tag3']),
                WikiContrib(1003, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['tag1', 'tag2', 'tag4']),
            ]),
            CacheableUserContribs([
                WikiContrib(2001, datetime(2020, 1, 4), 'Wilma', 0, 'Title', 'comment', tags=['tag1', 'tag3']),
                WikiContrib(2002, datetime(2020, 1, 5), 'Wilma', 0, 'Title', 'comment', tags=['tag1', 'tag2']),
            ]),
        ]
        self.force_login()

        response = self.client.get('/spi/timeline/Foo', {'users': ['Fred', 'Wilma']})

        mock_CacheableUserContribs.get.assert_has_calls([
            call(self.mock_wiki, 'Fred'),
            call(self.mock_wiki, 'Wilma')
        ])
        self.assertEqual(response.context['tag_table'],
                         [('Fred', [('tag1', 2), ('tag2', 2), ('tag3', 1), ('tag4', 1)]),
                          ('Wilma', [('tag1', 2), ('tag2', 1), ('tag3', 1), ('tag4', 0)])]
                         )


    def test_hidden_contribution_comments_render_as_hidden(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 1), 'Fred', 0, 'Title', None, tags=[]),
        ]
        self.force_login()

        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 1001, 'Fred', 'edit', '', 'Title', '<comment hidden>', ''),
        ])


    def test_hidden_log_comments_render_as_hidden(self):
        self.mock_wiki.user_log_events.return_value = [
            LogEvent(1,
                     datetime(2020, 1, 1),
                     'Fred',
                     'Title',
                     'create',
                     'create',
                     None),
            ]

        self.force_login()

        response = self.client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 1, 'Fred', 'create', 'create', 'Title', '<comment hidden>', ''),
        ])
