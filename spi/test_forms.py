from unittest import TestCase
from spi.forms import SockSelectForm
from django.forms import BooleanField
from pprint import pprint

class SockSelectFormTest(TestCase):
    def test_build(self):
        form = SockSelectForm.build(['s0', 's1'])
        self.assertIsInstance(form, SockSelectForm)
        self.assertIsInstance(form.fields['sock0'], BooleanField)
        self.assertIsInstance(form.fields['sock1'], BooleanField)
