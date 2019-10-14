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

        expected = {CategoryGraph('c1'),
                    CategoryGraph('c2'),
                    }

        self.assertEqual(views._get_categories('page', 3),
                         expected)

    def test_get_categories_empty_set(self):
        self.install_mock({
            'page': {},
        })

        expected = set()

        self.assertEqual(views._get_categories('page', 3),
                         expected)

    def test_get_categories_two_deep(self):
        self.install_mock({
            'page': {'c1'},
            'c1': {'c2'},
        })

        expected = {CategoryGraph('c1', {CategoryGraph('c2')})}

        self.assertEqual(views._get_categories('page', 3),
                         expected)

    def test_get_categories_depth_limited(self):
        self.install_mock({
            'page': {'c1'},
            'c1': {'c2'},
            'c2': {'c3a', 'c3b'},
            'c3a': {'c4'},
            'c4': {'c5'},
        })

        expected = {
            CategoryGraph('c1',
                          {CategoryGraph('c2',
                                         {CategoryGraph('c3a'),
                                          CategoryGraph('c3b'),
                                          })})}

        self.assertEqual(views._get_categories('page', 3),
                         expected)

    def test_get_categories_multipath(self):
        self.install_mock({
            'page': {'c1', 'c2'},
            'c1': {'c3'},
            'c2': {'c3'},
        })

        expected = {
            CategoryGraph('c1', {CategoryGraph('c3')}),
            CategoryGraph('c2', {CategoryGraph('c3')})
            }

        self.assertEqual(views._get_categories('page', 3),
                         expected)

        
class CategoryGraphTest(TestCase):
    def test_construct_no_parents(self):
        g = CategoryGraph('c1')

        self.assertEqual(g.name, 'c1')
        self.assertEqual(g.parents, set())


    def test_construct_with_parent_set(self):
        g = CategoryGraph('c1', {CategoryGraph('c2')})

        self.assertEqual(g.name, 'c1')
        self.assertEqual(g.parents, {CategoryGraph('c2')})

        
    def test_flatten_with_no_parents(self):
        g = CategoryGraph('c1')

        expected = {'c1'}

        self.assertEqual(g.flatten(), expected)

        
    def test_flatten_with_parents(self):
        g = CategoryGraph('c1',
                          {CategoryGraph('c2',
                                         {CategoryGraph('c3a'),
                                          CategoryGraph('c3b')
                                         })})

        self.assertEqual(g.flatten(), {'c1', 'c2', 'c3a', 'c3b'})
