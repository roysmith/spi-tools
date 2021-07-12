from unittest.mock import patch

from spi.index_view import IndexView
from spi.test_views import ViewTestCase

# pylint: disable=invalid-name


class IndexViewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('spi.index_view')


    @patch('spi.forms.Wiki', autospec=True)
    @patch('spi.index_view.get_current_case_names', autospec=True)
    def test_unknown_button(self, mock_get_current_case_names, mock_Wiki):
        mock_Wiki().page_exists.return_value = True
        mock_get_current_case_names.return_value = ['blah']

        response = self.client.post('/spi/', {'case_name': ['Fred']})

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content, b'No known button in POST')


    @patch('spi.index_view.get_current_case_names', autospec=True)
    def test_generates_correct_case_names(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']

        data = IndexView.generate_select2_data('')
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Bob', 'text': 'Bob'}]
        self.assertEqual(data, expected_data)


    @patch('spi.index_view.get_current_case_names', autospec=True)
    def test_url_case_name_is_selected(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']

        data = IndexView.generate_select2_data('Bob')

        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Bob', 'text': 'Bob', 'selected': True}]
        self.assertEqual(data, expected_data)


    @patch('spi.index_view.get_current_case_names', autospec=True)
    def test_url_case_name_is_added_if_missing(self, mock_get_current_case_names):
        mock_get_current_case_names.return_value = ['Alice', 'Bob']

        data = IndexView.generate_select2_data('Arnold')
        expected_data = [{'id': '', 'text': ''},
                         {'id': 'Alice', 'text': 'Alice'},
                         {'id': 'Arnold', 'text': 'Arnold', 'selected': True},
                         {'id': 'Bob', 'text': 'Bob'}]
        self.assertEqual(data, expected_data)


    @patch('spi.index_view.get_current_case_names', autospec=True)
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
