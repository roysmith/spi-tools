from . import views
from unittest import TestCase
from unittest.mock import MagicMock


class ViewTestCase(TestCase):
    def install_mock(self, value_dict):
        """Installs a MagicMock object configured to return specific values,
        held in values_dict; this is a mapping from arguments to return values.
        """
        views._get_category_names = MagicMock(
            side_effect=lambda x: value_dict.get(x, set()))

    def test_get_categories_no_parents(self):
        self.install_mock({
            'page': {'c1', 'c2'},
        })
        self.assertEqual(views._get_categories('page', 3),
                         {views.CategoryGraph('c1'),
                          views.CategoryGraph('c2')
                         })

    def test_get_categories_empty_set(self):
        self.install_mock({
            'page': {},
        })
        self.assertEqual(views._get_categories('page', 3),
                         set())
