import os
from django.test import TestCase

from . import views


class SPIArchiveTestCase(TestCase):
    def test_get_master_name(self):
        text = '''
        {{SPIarchive notice|1=KaranSharma0445}}
        '''
        archive = views.SPIArchive(text)
        expected =  'KaranSharma0445'
        self.assertEqual(archive.master_name(), expected)


    def test_get_socks(self):
        text = '''
        * {{checkuser|1=Sharvind Page}}
        * {{checkuser|1=PoSharvind}}
        * {{checkIP|86.170.34.216}}
        '''
        archive = views.SPIArchive(text)
        expected =  {'Sharvind Page', 'PoSharvind', '86.170.34.216'}
        self.assertEqual(archive.socks(), expected)


    def test_get_socks_extra_whitespace(self):
        text = '''
        * {{checkuser|1=DipikaKakar346 }}
        '''
        archive = views.SPIArchive(text)
        expected =  {'DipikaKakar346'}
        self.assertEqual(archive.socks(), expected)
