from unittest.mock import patch, MagicMock
import textwrap
from datetime import datetime
import json

from lxml import etree

from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model


from wiki_interface.data import WikiContrib, LogEvent
from wiki_interface.block_utils import BlockEvent
from spi.views import SockSelectView, UserSummary, TimelineEvent, ValidatedUser


class IndexViewTest(TestCase):
    # pylint: disable=invalid-name


    @patch('spi.forms.Wiki')
    def test_unknown_button(self, mock_Wiki):
        mock_Wiki().page_exists.return_value = True
        client = Client()

        response = client.post('/spi/', {'case_name': ['Fred']})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spi/index.dtl')
        self.assertTrue(response.context['error'].startswith('No known button in POST'))
        self.assertRegex(response.content, b'No known button in POST')


    @patch('spi.views.get_current_case_names')
    def test_renders_correct_case_names(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']
        client = Client()

        response = client.get('/spi/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['choices'])
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Bob', 'text': 'Bob'}]
        self.assertEqual(data, expected_data)


    @patch('spi.views.get_current_case_names')
    def test_url_case_name_is_selected(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']
        client = Client()

        response = client.get('/spi/?caseName=Bob')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['choices'])
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Bob', 'text': 'Bob', 'selected': True}]
        self.assertEqual(data, expected_data)


    @patch('spi.views.get_current_case_names')
    def test_url_case_name_is_added_if_missing(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']
        client = Client()

        response = client.get('/spi/?caseName=Arnold')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['choices'])
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Arnold', 'text': 'Arnold', 'selected': True},
                         {'id': 'Bob', 'text': 'Bob'}]
        self.assertEqual(data, expected_data)


    @patch('spi.views.get_current_case_names')
    def test_cases_names_with_spaces_are_deduplicated(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Adhithya Kiran Chekavar']
        client = Client()

        response = client.get('/spi/?caseName=Adhithya%20Kiran%20Chekavar')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['choices'])
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Adhithya Kiran Chekavar',
                          'text': 'Adhithya Kiran Chekavar',
                          'selected': True}]
        self.assertEqual(data, expected_data)


class SockSelectViewTest(TestCase):
    # pylint: disable=invalid-name

    def test_build_context(self):
        case_name = "Foo"
        user_infos = [ValidatedUser("User1", "20 June 2020", True),
                      ValidatedUser("User2", "21 June 2020", True),
                      ValidatedUser("User3", "21 June 2020", False),
                      ]

        context = SockSelectView.build_context(case_name, user_infos)

        self.assertEqual(context['case_name'], "Foo")
        self.assertEqual(context['invalid_users'],
                         [ValidatedUser("User3", "21 June 2020", False)])
        expected_items = {('User1', 'User1', '20 June 2020'),
                          ('User2', 'User2', '21 June 2020')}
        items = {(field.label, name, date)
                 for field, name, date in context['form_info']}
        self.assertEqual(items, expected_items)


    def test_build_context_deduplicates_users(self):
        case_name = "Foo"
        user_infos = [ValidatedUser("User1", "20 June 2020", True),
                      ValidatedUser("User1", "20 June 2020", True),
                      ValidatedUser("User2", "21 June 2020", True)]

        context = SockSelectView.build_context(case_name, user_infos)

        self.assertEqual(context['case_name'], "Foo")
        self.assertEqual(context['invalid_users'], [])
        expected_items = {('User1', 'User1', '20 June 2020'),
                          ('User2', 'User2', '21 June 2020')}
        items = {(field.label, name, date)
                 for field, name, date in context['form_info']}
        self.assertEqual(items, expected_items)


    @patch('wiki_interface.wiki.Site')
    def test_mismatched_quotes(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = textwrap.dedent(
            """
            ===31 January 2020===

            ''Blah

            ===4 February 2020===

            ''Blah Blah
            """)
        client = Client()
        response = client.get('/spi/sock-select/Foo/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spi/sock-select.dtl')


    @patch('spi.views.get_sock_names')
    def test_context_includes_unique_dates(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("User1", "20 June 2020", True),
            ValidatedUser("User2", "21 June 2020", True),
            ValidatedUser("User3", "21 June 2020", True),
        ]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.assertEqual(response.context['dates'], ['20 June 2020', '21 June 2020'])


    @patch('spi.views.get_sock_names')
    def test_context_dates_are_sorted_corretly(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("User", "08 October 2020", True),
            ValidatedUser("User", "10 December 2019", True),
            ValidatedUser("User", "12 December 2019", True),
            ValidatedUser("User", "12 July 2020", True),
            ValidatedUser("User", "15 December 2020", True),
            ValidatedUser("User", "15 May 2020", True),
        ]
        client = Client()

        response = client.get('/spi/sock-select/Foo/')

        self.assertEqual(response.context['dates'],
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


class UserSummaryTest(TestCase):
    def test_urlencoded_username(self):
        summary = UserSummary('foo', '20 July 2020')
        self.assertEqual(summary.username, 'foo')
        self.assertEqual(summary.urlencoded_username(), 'foo')

    def test_urlencoded_username_with_slash(self):
        summary = UserSummary('foo/bar', '20 July 2020')
        self.assertEqual(summary.username, 'foo/bar')
        self.assertEqual(summary.urlencoded_username(), 'foo%2Fbar')


class SockInfoViewTest(TestCase):
    # pylint: disable=invalid-name

    @patch('mwclient.Site', new_callable=MagicMock, spec=['pages', 'users'])
    def test_get_with_empty_mw_queries_renders_one_summary(self, mock_Site):
        mock_site = mock_Site()
        mock_site.pages.__getitem__().text.return_value = ''
        mock_site.users().return_value = iter([{}])
        client = Client()
        response = client.get('/spi/sock-info/Foo/')
        self.assertTemplateUsed(response, 'spi/sock-info.dtl')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['case_name'], 'Foo')
        self.assertEqual(response.context['summaries'], [UserSummary('Foo', None)])


class UserActivitiesViewTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.views.Wiki')
    def test_mainspace_title_contains_colon(self, mock_Wiki):
        mock_Wiki().user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 1), 'Fred', 0, 'Batman: xxx', 'comment')]
        mock_Wiki().deleted_user_contributions.return_value = []
        mock_Wiki().namespace_values = {'': 0, 'Draft': 2}

        user_fred = get_user_model().objects.create_user('Fred')
        client = Client()
        client.force_login(user_fred, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/user-activities/Foo', {'count': 10, 'main': 1}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spi/user-activities.dtl')
        edit_data = response.context['daily_activities'][0]
        self.assertEqual(edit_data,
                         ('primary', datetime(2020, 1, 1), 'edit', 'Batman: xxx', 'comment'))


class TimelineViewTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.views.Wiki')
    def test_event_list(self, mock_Wiki):
        mock_Wiki().user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment'),
            WikiContrib(datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment'),
        ]
        mock_Wiki().deleted_user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', False)]
        mock_Wiki().get_user_blocks.return_value = [
            BlockEvent('Wilma', datetime(2020, 2, 1))]
        mock_Wiki().get_user_log_events.return_value = [
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


    @patch('spi.views.Wiki')
    def test_edit_event_includes_tags(self, mock_Wiki):
        mock_Wiki().user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', is_live=True, tags=[]),
            WikiContrib(datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', is_live=True, tags=['tag']),
            WikiContrib(datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', is_live=True, tags=['tag1', 'tag2']),
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


    @patch('spi.views.Wiki')
    def test_deleted_edit_event_includes_tags(self, mock_Wiki):
        mock_Wiki().user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', is_live=False, tags=['tag1', 'tag2']),
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        # pylint: disable=line-too-long
        self.assertEqual(response.context['events'], [
            TimelineEvent(datetime(2020, 1, 3), 'Fred', 'edit', 'deleted', 'Title', 'comment', 'tag1, tag2'),
        ])


    @patch('spi.views.Wiki')
    def test_html_includes_tags(self, mock_Wiki):
        mock_Wiki().user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['my test tag']),
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        tree = etree.HTML(response.content)
        extras = tree.cssselect('#events div.extra')
        self.assertEqual([e.text for e in extras], ['my test tag'])


    @patch('spi.views.Wiki')
    def test_context_includes_tag_list(self, mock_Wiki):
        mock_Wiki().user_contributions.return_value = [
            WikiContrib(datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', tags=[]),
            WikiContrib(datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', tags=['tag']),
            WikiContrib(datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['tag1', 'tag2', 'tag4']),
            WikiContrib(datetime(2020, 1, 4), 'Wilma', 0, 'Title', 'comment', tags=['tag1', 'tag3']),
            WikiContrib(datetime(2020, 1, 5), 'Barney', 0, 'Title', 'comment', tags=['tag1', 'tag2']),
        ]
        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['u1']})

        self.assertEqual(response.context['tag_list'], ['tag', 'tag1', 'tag2', 'tag3', 'tag4'])


    @patch('spi.views.Wiki')
    def test_context_includes_tag_table(self, mock_Wiki):
        def mock_user_contributions(user_name):
            if user_name == 'Fred':
                return [WikiContrib(datetime(2020, 1, 1), 'Fred', 0, 'Title', 'comment', tags=[]),
                        WikiContrib(datetime(2020, 1, 2), 'Fred', 0, 'Title', 'comment', tags=['tag1', 'tag2', 'tag3']),
                        WikiContrib(datetime(2020, 1, 3), 'Fred', 0, 'Title', 'comment', tags=['tag1', 'tag2', 'tag4'])]
            if user_name == 'Wilma':
                return [WikiContrib(datetime(2020, 1, 4), 'Wilma', 0, 'Title', 'comment', tags=['tag1', 'tag3']),
                        WikiContrib(datetime(2020, 1, 5), 'Wilma', 0, 'Title', 'comment', tags=['tag1', 'tag2'])]
            return []

        mock_Wiki().user_contributions.side_effect = mock_user_contributions

        user_u1 = get_user_model().objects.create_user('U1')
        client = Client()
        client.force_login(user_u1, backend='django.contrib.auth.backends.ModelBackend')
        response = client.get('/spi/timeline/Foo', {'users': ['Fred', 'Wilma']})

        self.assertEqual(response.context['tag_table'],
                         [('Fred', [('tag1', 2), ('tag2', 2), ('tag3', 1), ('tag4', 1)]),
                          ('Wilma', [('tag1', 2), ('tag2', 1), ('tag3', 1), ('tag4', 0)])]
                         )
