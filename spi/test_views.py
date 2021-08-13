from unittest.mock import patch

from django.test import TestCase
from django.test import Client
from django.test.signals import template_rendered
from django.contrib.auth import get_user_model
from django.shortcuts import render

# pylint: disable=invalid-name


class ViewTestCase(TestCase):
    """Base class for all SPI view tests.

    Subclass this and have setUp() call super().setUp('spi.my_view')
    for a view defined in my_view.py.

    """
    @staticmethod
    def render_patch(request, template, context):
        """Work-around for the django test client not working properly with
        jinga2 templates (https://code.djangoproject.com/ticket/24622).

        """
        template_rendered.send(sender=None, template=template, context=context)
        return render(request, template, context)


    def force_login(self):
        """Call this when testing LoginRequired views.

        """
        user = get_user_model().objects.create_user('my-test-user')
        self.client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')


    #pylint: disable=arguments-differ
    def setUp(self, view_module_name):
        render_patcher = patch(f'{view_module_name}.render', autospec=True)
        self.mock_render = render_patcher.start()
        self.mock_render.side_effect = self.render_patch
        self.addCleanup(render_patcher.stop)

        wiki_patcher = patch(f'{view_module_name}.Wiki', autospec=True)
        MockWikiClass = wiki_patcher.start()
        self.mock_wiki = MockWikiClass()
        self.addCleanup(wiki_patcher.stop)

        # In theory, we've patched Wiki so this should be a no-op.
        # It's just here to catch anyplace where we might have missed
        # patching something and should prevent any actual network
        # traffic from leaking.
        site_patcher = patch('wiki_interface.wiki.Site', autospec=True)
        MockSiteClass = site_patcher.start()
        MockSiteClass.side_effect = RuntimeError
        self.addCleanup(site_patcher.stop)

        self.client = Client()
