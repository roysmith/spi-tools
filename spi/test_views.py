from unittest.mock import patch, MagicMock
import textwrap
from datetime import datetime
import json

from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model


from wiki_interface.data import WikiContrib
from spi.views import SockSelectView, UserSummary
from spi.spi_utils import SpiUserInfo


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


class SockSelectViewTest(TestCase):
    # pylint: disable=invalid-name

    def test_build_context(self):
        case_name = "Foo"
        user_infos = [SpiUserInfo("User1", "20 June 2020"),
                      SpiUserInfo("User2", "21 June 2020")]

        context = SockSelectView.build_context(case_name, user_infos)

        self.assertEqual(context['case_name'], "Foo")
        expected_items = {('User1', 'User1', '20 June 2020'),
                          ('User2', 'User2', '21 June 2020')}
        items = {(field.label, name, date)
                 for field, name, date in context['form_info']}
        self.assertEqual(items, expected_items)


    def test_build_context_deduplicates_users(self):
        case_name = "Foo"
        user_infos = [SpiUserInfo("User1", "20 June 2020"),
                      SpiUserInfo("User1", "20 June 2020"),
                      SpiUserInfo("User2", "21 June 2020")]

        context = SockSelectView.build_context(case_name, user_infos)

        self.assertEqual(context['case_name'], "Foo")
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
