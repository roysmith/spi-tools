import textwrap
from unittest.mock import patch

from lxml import etree

from spi.spi_utils import CacheableSpiCase
from spi.test_views import ViewTestCase
from spi.views import ValidatedUser

# pylint: disable=invalid-name

class SockSelectViewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('spi.sock_select_view')


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_context_is_correct(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True),
                                            ValidatedUser("User3", "21 June 2020", False)]

        response = self.client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['case_name'], "Foo")
        self.assertEqual(context['invalid_users'], [ValidatedUser("User3", "21 June 2020", False)])
        self.assertEqual({(field.label, name, date) for field, name, date in context['form_info']},
                         {('User1', 'User1', '20 June 2020'), ('User2', 'User2', '21 June 2020')})


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_users_are_deduplicated(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True)]

        response = self.client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['case_name'], "Foo")
        self.assertEqual(context['invalid_users'], [])
        self.assertEqual({(field.label, name, date) for field, name, date in context['form_info']},
                         {('User1', 'User1', '20 June 2020'), ('User2', 'User2', '21 June 2020')})


    @patch('wiki_interface.wiki.Site')  # autospec fails here, not sure why
    @patch('spi.views.CacheableSpiCase', autospec=True)
    def test_mismatched_quotes(self, mock_CacheableSpiCase, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = textwrap.dedent(
            """
            ===31 January 2020===

            ''Blah

            ===4 February 2020===

            ''Blah Blah
            """)
        mock_CacheableSpiCase.get.return_value = CacheableSpiCase('Fred')

        response = self.client.get('/spi/sock-select/Foo/')

        self.assertEqual(response.status_code, 200)


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_context_includes_unique_dates(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True),
                                            ValidatedUser("User3", "21 June 2020", True)]

        response = self.client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['dates'], ['21 June 2020', '20 June 2020'])


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_context_dates_are_sorted_in_reverse_chronological_order(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [ValidatedUser("User", "08 October 2020", True),
                                            ValidatedUser("User", "10 December 2019", True),
                                            ValidatedUser("User", "12 December 2019", True),
                                            ValidatedUser("User", "12 July 2020", True),
                                            ValidatedUser("User", "15 December 2020", True),
                                            ValidatedUser("User", "15 May 2020", True)]

        response = self.client.get('/spi/sock-select/Foo/')

        self.mock_render.assert_called_once()
        context = response.context[0]
        self.assertEqual(context['dates'],
                         ['15 December 2020',
                          '08 October 2020',
                          '12 July 2020',
                          '15 May 2020',
                          '12 December 2019',
                          '10 December 2019',
                         ])


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_html_date_classes(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("User1", "20 June 2020", True),
            ValidatedUser("User2", "21 June 2020", True),
            ValidatedUser("User3", "21 June 2020", True),
            ValidatedUser("User4", "21 June 2020", True),
        ]

        response = self.client.get('/spi/sock-select/Foo/')

        tree = etree.HTML(response.content)
        self.assertEqual(len(tree.cssselect('td.spi-date-20June2020 > input[type=checkbox]')), 1)
        self.assertEqual(len(tree.cssselect('td.spi-date-21June2020 > input[type=checkbox]')), 3)


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_html_includes_dropdown(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("User1", "20 June 2020", True),
            ValidatedUser("User2", "21 June 2020", True),
            ValidatedUser("User3", "21 June 2020", True),
        ]

        response = self.client.get('/spi/sock-select/Foo/')

        tree = etree.HTML(response.content)
        buttons = tree.cssselect('div.dropdown-menu > button.dropdown-item[type=button]')
        self.assertEqual([b.get('data-date') for b in buttons], ['21June2020', '20June2020'])


    @patch('spi.sock_select_view.get_sock_names', autospec=True)
    def test_usernames_are_escaped_in_html(self, mock_get_sock_names):
        mock_get_sock_names.return_value = [
            ValidatedUser("foo&bar", "20 June 2020", True),
        ]

        response = self.client.get('/spi/sock-select/Foo/')

        tree = etree.HTML(response.content)
        checkbox = tree.cssselect('#sock-table > tr > td > input[type=checkbox]')[0]
        self.assertEqual(checkbox.get('name'), 'sock_foo%26bar')
        self.assertEqual(checkbox.get('id'), 'id_sock_foo%26bar')
        label = tree.cssselect('#sock-table > tr > td > label')[0]
        self.assertEqual(label.get('for'), 'id_sock_foo%26bar')
        self.assertEqual(label.text, 'foo&bar')
