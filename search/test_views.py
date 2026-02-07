from unittest.mock import patch
import unittest
from pprint import pprint
import os
import pytest

from django.conf import settings
from django.test import TestCase, Client
from django.test.signals import template_rendered
from django.shortcuts import render

from search.forms import SearchForm

#
# Note: this should be refactored with spi.test_views.py
#

# pylint: disable=invalid-name

@pytest.mark.skipif('GITHUB_ACTION' in os.environ, reason='Does not work on github')
class ViewTestCase(TestCase):
    """Base class for all search view tests.

    Subclass this and have setUp() call super().setUp('search.my_view')
    for a view defined in my_view.py.

    """
    @staticmethod
    def render_patch(request, template, context):
        """Work-around for the django test client not working properly with
        jinga2 templates (https://code.djangoproject.com/ticket/24622).

        """
        template_rendered.send(sender=None, template=template, context=context)
        return render(request, template, context)


    #pylint: disable=arguments-differ
    def setUp(self, view_module_name):
        render_patcher = patch(f'{view_module_name}.render', autospec=True)
        self.mock_render = render_patcher.start()
        self.mock_render.side_effect = self.render_patch
        self.addCleanup(render_patcher.stop)

        # wiki_patcher = patch(f'{view_module_name}.Wiki', autospec=True)
        # MockWikiClass = wiki_patcher.start()
        # self.mock_wiki = MockWikiClass()
        # self.addCleanup(wiki_patcher.stop)

        # # In theory, we've patched Wiki so this should be a no-op.
        # # It's just here to catch anyplace where we might have missed
        # # patching something and should prevent any actual network
        # # traffic from leaking.
        # site_patcher = patch('wiki_interface.wiki.Site', autospec=True)
        # MockSiteClass = site_patcher.start()
        # MockSiteClass.side_effect = RuntimeError
        # self.addCleanup(site_patcher.stop)

        self.client = Client()



class IndexViewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('search.views')


    def test_get_returns_200(self):
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)


    def test_get_renders_index_template(self):
        response = self.client.get('/search/')
        self.assertEqual(response.templates[0], 'search/index.html')


    def test_post_renders_results_template(self):
        data = {'search_terms': 'foo'}
        os_result = {'_shards': {'failed': 0, 'skipped': 0, 'successful': 1, 'total': 1},
                     'hits': {'hits': [{'_id': 'GKgpmn4B8Fs0LHO50FIx',
                                        '_index': 'spi-tools-dev-es-index',
                                        '_score': 4.292108,
                                        '_source': {'comment': 'blah, blah',
                                                    'page_id': 5399120,
                                                    'rev_id': 945483029,
                                                    'user': 'SMcCandlish'},
                                        '_type': '_doc'}],
                              'max_score': 4.292108,
                              'total': {'relation': 'eq', 'value': 1}},
                     'timed_out': False,
                     'took': 2}
        with patch('search.views.OpenSearch') as mock_os:
            mock_os().search.return_value = os_result
            response = self.client.post('/search/', data)
        self.assertEqual(response.templates[0], 'search/results.html')
        self.assertEqual(response.context['results'], [{'comment': 'blah, blah',
                                                        'page_id': 5399120,
                                                        'rev_id': 945483029,
                                                        'user': 'SMcCandlish',
                                                        }])
