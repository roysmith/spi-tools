from unittest.mock import patch, NonCallableMock
from unittest import TestCase
import urllib.parse

from django.forms import BooleanField

from spi.forms import CaseNameForm, SockSelectForm
from wiki_interface import Wiki


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


class CaseNameFormTest(TestCase):
    # pylint: disable=invalid-name

    def test_validate_with_valid_case_name(self):
        wiki = NonCallableMock(Wiki)
        wiki.page_exists.return_value = True
        data = {'case_name': 'Fred',
                }

        form = CaseNameForm(data, wiki=wiki)

        self.assertTrue(form.is_valid())


    def test_validate_with_invalid_case_name(self):
        wiki = NonCallableMock(Wiki)
        wiki.page_exists.return_value = False
        data = {'case_name': 'Fred',
                }

        form = CaseNameForm(data, wiki=wiki)

        self.assertFalse(form.is_valid())
        errors = form.errors.as_data()
        self.assertCountEqual(errors.keys(), ['case_name'])
        self.assertEqual(len(errors['case_name']), 1)
        self.assertEqual(errors['case_name'][0].code, 'invalid_choice')
