from . import views
from unittest import TestCase
from unittest.mock import MagicMock


class ViewTestCase(TestCase):
    def test_get_category_tree(self):
        values = {
            'Margaret Sibella Brown': {'c1', 'c2'},
            'c1': {'c3'},
            }
        views._get_page_categories = MagicMock(side_effect=lambda x: values.get(x, set()))
        categories = views._get_category_tree('Margaret Sibella Brown', 3)
        self.assertEqual(categories, {'c1', 'c2', 'c3'})
        
