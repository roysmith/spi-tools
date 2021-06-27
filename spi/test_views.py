from unittest.mock import patch, call
import unittest
import textwrap
from datetime import datetime

from lxml import etree

from django.test import TestCase
from django.test import Client
from django.test.signals import template_rendered
from django.contrib.auth import get_user_model
from django.shortcuts import render

from wiki_interface.data import WikiContrib, LogEvent
from wiki_interface.block_utils import BlockEvent
from spi.views import SockSelectView, UserSummary, TimelineEvent, ValidatedUser, IndexView, PagesView
from spi.spi_utils import CacheableSpiCase
from spi.user_utils import CacheableUserContribs


class ViewTestCase(TestCase):
    @staticmethod
    def render_patch(request, template, context):
        template_rendered.send(sender=None, template=template, context=context)
        return render(request, template, context)


    def setUp(self):
        render_patcher = patch('spi.views.render')
        self.mock_render = render_patcher.start()
        self.mock_render.side_effect = self.render_patch
        self.addCleanup(render_patcher.stop)

        wiki_patcher = patch('spi.views.Wiki')
        MockWikiClass = wiki_patcher.start()
        self.mock_wiki = MockWikiClass()
        self.addCleanup(wiki_patcher.stop)


# For reasons that are not clear, test_unknown_button() fails (killed)
# when inheriting from ViewTestCase.  It is obviously some interaction
# between patching spi.forms.Wiki and pathing spi.views.Wiki, but that
# doesn't make sense.  Breaking that one test out into a class that
# doesn't inherit from ViewTestCase is a hack, but works around the
# problem.
class IndexViewFormTest(TestCase):
    @patch('spi.forms.Wiki')
    def test_unknown_button(self, mock_Wiki):
        mock_Wiki().page_exists.return_value = True
        client = Client()

        response = client.post('/spi/', {'case_name': ['Fred']})

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content, b'No known button in POST')


class IndexViewTest(ViewTestCase):
    # pylint: disable=invalid-name

    @patch('spi.views.get_current_case_names')
    def test_generates_correct_case_names(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']

        data = IndexView.generate_select2_data('')
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Bob', 'text': 'Bob'}]
        self.assertEqual(data, expected_data)


    @patch('spi.views.get_current_case_names')
    def test_url_case_name_is_selected(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']

        data = IndexView.generate_select2_data('Bob')

        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Bob', 'text': 'Bob', 'selected': True}]
        self.assertEqual(data, expected_data)


    @patch('spi.views.get_current_case_names')
    def test_url_case_name_is_added_if_missing(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']

        data = IndexView.generate_select2_data('Arnold')
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Arnold', 'text': 'Arnold', 'selected': True},
                         {'id': 'Bob', 'text': 'Bob'}]
        self.assertEqual(data, expected_data)


    @patch('spi.views.get_current_case_names')
    def test_deduplicates_case_name_with_sock_names(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Adhithya Kiran Chekavar',
                                                    'Fred']
        data = IndexView.generate_select2_data('Adhithya Kiran Chekavar')
        expected_data = [{'id': '',
                          'text': ''},
                         {'id': 'Adhithya Kiran Chekavar',
                          'text': 'Adhithya Kiran Chekavar',
                          'selected': True},
                         {'id': 'Fred',
                          'text': 'Fred'},
                         ]
        self.assertEqual(data, expected_data)


class SockSelectViewTest(ViewTestCase):
    # pylint: disable=invalid-name

    @patch('spi.views.get_sock_names')
    def test_context_is_correct(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True),
                                            ValidatedUser("User3", "21 June 2020", False)]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['case_name'], "Foo")
        self.assertEqual(context['invalid_users'], [ValidatedUser("User3", "21 June 2020", False)])
        self.assertEqual({(field.label, name, date) for field, name, date in context['form_info']},
                         {('User1', 'User1', '20 June 2020'), ('User2', 'User2', '21 June 2020')})


    @patch('spi.views.get_sock_names')
    def test_users_are_deduplicated(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True)]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.mock_render.atassert_called_once()
        context = response.context[0]
        self.assertEqual(context['case_name'], "Foo")
        self.assertEqual(context['invalid_users'], [])
        self.assertEqual({(field.label, name, date) for field, name, date in context['form_info']},
                         {('User1', 'User1', '20 June 2020'), ('User2', 'User2', '21 June 2020')})


    @patch('wiki_interface.wiki.Site')
    @patch('spi.views.CacheableSpiCase')
    def test_mismatched_quotes(self, mock_CacheableSpiCase, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = textwrap.dedent(
            """
            ===31 January 2020===

            ''Blah

            ===4 February 2020===

            ''Blah Blah
            """)
        mock_CacheableSpiCase.get.return_value = CacheableSpiCase('Fred')
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.assertEqual(response.status_code, 200)


    @patch('spi.views.get_sock_names')
    def test_context_includes_unique_dates(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True),
                                            ValidatedUser("User3", "21 June 2020", True)]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['dates'], ['20 June 2020', '21 June 2020'])


    @patch('spi.views.get_sock_names')
    def test_context_dates_are_sorted_in_chronological_order(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User", "08 October 2020", True),
                                            ValidatedUser("User", "10 December 2019", True),
                                            ValidatedUser("User", "12 December 2019", True),
                                            ValidatedUser("User", "12 July 2020", True),
                                            ValidatedUser("User", "15 December 2020", True),
                                            ValidatedUser("User", "15 May 2020", True)]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['dates'],
                         ['10 December 2019',
                          '12 December 2019',
                          '15 May 2020',
                          '12 July 2020',
                          '08 October 2020',
                          '15 December 2020',
                         ])


    @patch('spi.views.get_sock_names')
    def test_html_date_classes(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("User1", "20 June 2020", True),
            ValidatedUser("User2", "21 June 2020", True),
            ValidatedUser("User3", "21 June 2020", True),
            ValidatedUser("User4", "21 June 2020", True),
        ]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        tree = etree.HTML(response.content)
        self.assertEqual(len(tree.cssselect('td.spi-date-20June2020 > input[type=checkbox]')), 1)
        self.assertEqual(len(tree.cssselect('td.spi-date-21June2020 > input[type=checkbox]')), 3)


    @patch('spi.views.get_sock_names')
    def test_html_includes_dropdown(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("User1", "20 June 2020", True),
            ValidatedUser("User2", "21 June 2020", True),
            ValidatedUser("User3", "21 June 2020", True),
        ]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        tree = etree.HTML(response.content)
        buttons = tree.cssselect('div.dropdown-menu > button.dropdown-item[type=button]')
        self.assertEqual([b.get('data-date') for b in buttons], ['20June2020', '21June2020'])


    @patch('spi.views.get_sock_names')
    def test_usernames_are_escaped_in_html(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("foo&bar", "20 June 2020", True),
        ]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        tree = etree.HTML(response.content)
        checkbox = tree.cssselect('#sock-table > tr > td > input[type=checkbox]')[0]
        self.assertEqual(checkbox.get('name'), 'sock_foo%26bar')
        self.assertEqual(checkbox.get('id'), 'id_sock_foo%26bar')
        label = tree.cssselect('#sock-table > tr > td > label')[0]
        self.assertEqual(label.get('for'), 'id_sock_foo%26bar')
        self.assertEqual(label.text, 'foo&bar')


class UserSummaryTest(ViewTestCase):
    def test_urlencoded_username(self):
        summary = UserSummary('foo', '20 July 2020')
        self.assertEqual(summary.username, 'foo')
        self.assertEqual(summary.urlencoded_username(), 'foo')

    def test_urlencoded_username_with_slash(self):
        summary = UserSummary('foo/bar', '20 July 2020')
        self.assertEqual(summary.username, 'foo/bar')
        self.assertEqual(summary.urlencoded_username(), 'foo%2Fbar')


class TimelineViewTest(ViewTestCase):
    # pylint: disable=invalid-name


    def test_event_list(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(103, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment'),
            WikiContrib(101, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment'),
        ]
        self.mock_wiki.deleted_user_contributions.return_value = [
            WikiContrib(102, datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', False)]
        self.mock_wiki.user_blocks.return_value = [
            BlockEvent('Wilma', datetime(2020, 2, 1))]
        self.mock_wiki.user_log_events.return_value = [
            LogEvent(datetime(2019, 11, 29), 'Fred', 'Fred-sock', 'newusers', 'create2', 'testing')
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 2, 1), 'Wilma', 'block', '', 'indef', '', ''),
            TimelineEvent(datetime(2020, 1, 3), 'Fred', 'edit', '', 'Title', 'comment', ''),
            TimelineEvent(datetime(2020, 1, 2), 'Fred', 'edit', 'deleted', 'Title', 'comment', ''),
            TimelineEvent(datetime(2020, 1, 1), 'Fred', 'edit', '', 'Title', 'comment', ''),
            TimelineEvent(datetime(2019, 11, 29), 'Fred', 'newusers', 'create2', 'Fred-sock', 'testing', ''),
        ])


    def test_edit_event_includes_tags(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', is_live=True, tags=[]),
            WikiContrib(1002, datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', is_live=True, tags=['tag']),
            WikiContrib(1003, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', is_live=True, tags=['tag1', 'tag2']),
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 'Fred', 'edit', '', 'Title', 'comment', ''),
            TimelineEvent(datetime(2020, 1, 2), 'Fred', 'edit', '', 'Title', 'comment', 'tag'),
            TimelineEvent(datetime(2020, 1, 3), 'Fred', 'edit', '', 'Title', 'comment', 'tag1, tag2'),
        ])


    def test_deleted_edit_event_includes_tags(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', is_live=False, tags=['tag1', 'tag2']),
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 3), 'Fred', 'edit', 'deleted', 'Title', 'comment', 'tag1, tag2'),
        ])


    def test_html_includes_tags(self):
        self.mock_wiki.user_contributions.return_value = [
            WikiContrib(1001, datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['my test tag']),
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

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
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.templates, ['spi/timeline.html'])
        self.assertEqual(response.context['tag_list'], ['tag', 'tag1', 'tag2', 'tag3', 'tag4'])


    @patch('spi.views.CacheableUserContribs')
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
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/timeline/Foo', {'users': ['Fred', 'Wilma']})

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
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 'Fred', 'edit', '', 'Title', '<comment hidden>', ''),
        ])


    def test_hidden_log_comments_render_as_hidden(self):
        self.mock_wiki.user_log_events.return_value = [
            LogEvent(datetime(2020, 1, 1),
                     'Fred',
                     'Title',
                     'create',
                     'create',
                     None),
            ]

        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 1), 'Fred', 'create', 'create', 'Title', '<comment hidden>', ''),
        ])


class PagesViewTest(ViewTestCase):
    # pylint: disable=invalid-name


    def test_get_uses_correct_template(self):
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/pages/Foo', {'users': ['u1']})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates, ['spi/pages.html'])


    @patch('spi.views.CacheableUserContribs')
    def test_get_page_data(self, mock_CacheableUserContribs):
        wiki = self.mock_wiki
        mock_CacheableUserContribs.get.side_effect = [
            CacheableUserContribs([
                WikiContrib(103, datetime(2020, 1, 5), 'u1', 0, 'Title1', 'comment', tags=['mw-reverted']),
                WikiContrib(103, datetime(2020, 1, 3), 'u1', 0, 'Title2', 'comment', tags=['mw-reverted']),
                WikiContrib(103, datetime(2020, 1, 2), 'u1', 0, 'Title1', 'comment'),
            ]),
            CacheableUserContribs([
                WikiContrib(103, datetime(2020, 1, 5), 'u2', 0, 'Title1', 'comment', tags=['mw-reverted', 'mobile edit']),
                WikiContrib(103, datetime(2020, 1, 3), 'u2', 0, 'Title2', 'comment', tags=['mobile edit']),
                WikiContrib(103, datetime(2020, 1, 2), 'u2', 0, 'Title3', 'comment'),
            ]),
            CacheableUserContribs([
                WikiContrib(103, datetime(2020, 1, 5), 'u3', 0, 'Title1', 'comment'),
            ]),
        ]
        self.mock_wiki.deleted_user_contributions.side_effect = [
            [WikiContrib(102, datetime(2020, 2, 2), 'u1', 0, 'Title1', 'comment', is_live=False),
            ],
            [WikiContrib(102, datetime(2020, 2, 2), 'u2', 0, 'Title2', 'comment', is_live=False),
             WikiContrib(102, datetime(2020, 2, 1), 'u2', 0, 'Title3', 'comment', is_live=False),
            ],
            [WikiContrib(102, datetime(2020, 2, 2), 'u3', 0, 'Title4', 'comment', is_live=False),
            ],
        ]

        page_data = PagesView.get_page_data(self.mock_wiki, ['u1', 'u2', 'u3'])

        self.assertEqual(page_data.edit_counts['Title1'], 5)
        self.assertEqual(page_data.edit_counts,
                         {'Title1': 5,
                          'Title2': 3,
                          'Title3': 2,
                          'Title4': 1,
                          })
        self.assertEqual(page_data.editor_counts,
                         {'Title1': 3,
                          'Title2': 2,
                          'Title3': 1,
                          'Title4': 1 ,
                          })
        self.assertEqual(page_data.reverted_counts,
                         {'Title1': 2,
                          'Title2': 1,
                          })


    @patch('spi.views.CacheableUserContribs')
    def test_context_includes_page_data(self, mock_CacheableUserContribs):
        mock_CacheableUserContribs.get.return_value = CacheableUserContribs([])
        self.mock_wiki.deleted_user_contributions.return_value = []
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/pages/Foo', {'users': ['u1']})

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['page_data'], PagesView.PageData)


    @patch('spi.views.CacheableUserContribs')
    def test_context_make_correct_back_end_calls(self, mock_CacheableUserContribs):
        mock_CacheableUserContribs.get.return_value = CacheableUserContribs([])
        self.mock_wiki.deleted_user_contributions.return_value = []
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')

        response = client.get('/spi/pages/Foo', {'users': ['u1']})

        mock_CacheableUserContribs.get.assert_called_once_with(self.mock_wiki, 'u1')
        self.mock_wiki.deleted_user_contributions.assert_called_once_with('u1')
