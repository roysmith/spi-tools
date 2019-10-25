import os
from django.test import TestCase

from . import views


class SPICaseTestCase(TestCase):
    def test_get_master_name(self):
        text = '''
        {{SPIarchive notice|1=KaranSharma0445}}
        '''
        case = views.SPICase(text)
        expected =  'KaranSharma0445'
        self.assertEqual(case.master_name(), expected)


    def test_get_socks(self):
        text = '''
        * {{checkuser|1=Sharvind Page}}
        * {{checkuser|1=PoSharvind}}
        * {{checkIP|86.170.34.216}}
        '''
        case = views.SPICase(text)
        expected =  {'Sharvind Page', 'PoSharvind', '86.170.34.216'}
        self.assertEqual(case.socks(), expected)


    def test_get_socks_extra_whitespace(self):
        text = '''
        * {{checkuser|1=DipikaKakar346 }}
        '''
        case = views.SPICase(text)
        expected =  {'DipikaKakar346'}
        self.assertEqual(case.socks(), expected)
