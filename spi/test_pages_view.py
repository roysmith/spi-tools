from datetime import datetime
from unittest.mock import patch

from spi.pages_view import PagesView
from spi.test_views import ViewTestCase
from spi.user_utils import CacheableUserContribs
from wiki_interface.data import WikiContrib

# pylint: disable=invalid-name

class PagesViewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('spi.pages_view')


    def test_get_uses_correct_template(self):
        self.force_login()

        response = self.client.get('/spi/pages/Foo', {'users': ['u1']})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates, ['spi/pages.html'])


    @patch('spi.pages_view.CacheableUserContribs', spec=CacheableUserContribs)
    def test_get_page_data(self, mock_CacheableUserContribs):
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
                          'Title4': 1,
                          })
        self.assertEqual(page_data.reverted_counts,
                         {'Title1': 2,
                          'Title2': 1,
                          })


    @patch('spi.pages_view.CacheableUserContribs', spec=CacheableUserContribs)
    def test_context_includes_page_data(self, mock_CacheableUserContribs):
        mock_CacheableUserContribs.get.return_value = CacheableUserContribs([])
        self.mock_wiki.deleted_user_contributions.return_value = []
        self.force_login()

        response = self.client.get('/spi/pages/Foo', {'users': ['u1']})

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['page_data'], PagesView.PageData)


    @patch('spi.pages_view.CacheableUserContribs', spec=CacheableUserContribs)
    def test_context_make_correct_back_end_calls(self, mock_CacheableUserContribs):
        mock_CacheableUserContribs.get.return_value = CacheableUserContribs([])
        self.mock_wiki.deleted_user_contributions.return_value = []
        self.force_login()

        self.client.get('/spi/pages/Foo', {'users': ['u1']})

        mock_CacheableUserContribs.get.assert_called_once_with(self.mock_wiki, 'u1')
        self.mock_wiki.deleted_user_contributions.assert_called_once_with('u1')
