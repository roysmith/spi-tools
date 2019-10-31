from unittest import TestCase

from spi_utils import SPICase, ArchiveError


class SPICaseTest(TestCase):
    def test_wikitext_is_stored(self):
        text = '''
        foo
        '''
        case = SPICase(text)
        self.assertEqual(case.wikitext, text)


    def test_master_name_returns_correct_value(self):
        text = '''
        {{SPIarchive notice|1=KaranSharma0445}}
        '''
        case = SPICase(text)
        self.assertEqual(case.master_name(), 'KaranSharma0445')


    def test_master_name_with_no_archive_notice_raises_archive_error(self):
        text = '''
        * {{checkuser|1=DipikaKakar346 }}
        '''
        case = SPICase(text)
        with self.assertRaises(ArchiveError):
            case.master_name()


    def test_master_name_with_multiple_archive_notices_raises_archive_error(self):
        text = '''
        {{SPIarchive notice|1=Foo}}
        {{SPIarchive notice|1=Bar}}
        '''
        case = SPICase(text)
        with self.assertRaises(ArchiveError):
            case.master_name()
