from unittest import TestCase
import urllib.parse

from django.forms import BooleanField

from .forms import SockSelectForm

class SockSelectFormTest(TestCase):
    def test_build_with_simple_names(self):
        form = SockSelectForm.build(['s0', 's1'])
        self.assertIsInstance(form, SockSelectForm)
        self.assertIsInstance(form.fields['sock_s0'], BooleanField)
        self.assertIsInstance(form.fields['sock_s1'], BooleanField)

    def test_build_with_quote_name(self):
        name = 'foo"bar'
        quoted_name = urllib.parse.quote(name)
        form = SockSelectForm.build([name])
        self.assertIsInstance(form, SockSelectForm)
        self.assertIsInstance(form.fields['sock_' + quoted_name], BooleanField)
