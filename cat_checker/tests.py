from . import views
from .views import CategoryGraph

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

        actual = views._get_categories('page', 3)

        expected = {CategoryGraph('c1'),
                    CategoryGraph('c2'),
                    }
        self.assertEqual(actual, expected)

    def test_get_categories_empty_set(self):
        self.install_mock({
            'page': {},
        })

        actual = views._get_categories('page', 3)

        expected = set()
        self.assertEqual(actual, expected)

    def test_get_categories_two_deep(self):
        self.install_mock({
            'page': {'c1'},
            'c1': {'c2'},
        })

        actual = views._get_categories('page', 3)

        g = CategoryGraph('c1')
        g.parents = {CategoryGraph('c2')}
        expected = {g}
        self.assertEqual(actual, expected)

    def test_get_categories_depth_limited(self):
        self.install_mock({
            'page': {'c1'},
            'c1': {'c2'},
            'c2': {'c3a', 'c3b'},
            'c3a': {'c4'},
            'c4': {'c5'},
        })

        actual = views._get_categories('page', 3)

        g3a = CategoryGraph('c3a')
        g3b = CategoryGraph('c3b')
        g2 = CategoryGraph('c2')
        g2.parents = {g3a, g3b}
        g1 = CategoryGraph('c1')
        g1.parents = {g2}
        expected = {g1}
        self.assertEqual(actual, expected)

    def test_get_categories_multipath(self):
        self.install_mock({
            'page': {'c1', 'c2'},
            'c1': {'c3'},
            'c2': {'c3'},
        })

        actual = views._get_categories('page', 3)

        g3 = CategoryGraph('c3')
        g2 = CategoryGraph('c2')
        g2.parents = {g3}
        g1 = CategoryGraph('c1')
        g1.parents = {g3}
        expected = {g1, g2}
        self.assertEqual(actual, expected)
