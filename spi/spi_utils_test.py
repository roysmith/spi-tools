from unittest import TestCase
import textwrap
import os.path
import mwparserfromhell

from spi_utils import SPICase, SPICaseDay, SPICheckUser, SPICheckIP, ArchiveError


def make_code(text):
    return mwparserfromhell.parse(textwrap.dedent(text))


class SPICaseTest(TestCase):
    def test_single_wikitext_is_stored(self):
        text = '''
        {{SPIarchive notice|1=test-user}}
        foo
        '''
        case = SPICase(text)
        self.assertEqual(case.wikitexts, [text])


    def test_multiple_wikitexts_are_stored(self):
        text1 = '''
        {{SPIarchive notice|1=test-user}}
        foo
        '''
        text2 = '''
        {{SPIarchive notice|1=test-user}}
        bar
        '''
        case = SPICase(text1, text2)
        self.assertEqual(case.wikitexts, [text1, text2])


    def test_master_name_returns_correct_value(self):
        text = '''
        {{SPIarchive notice|1=KaranSharma0445}}
        '''
        case = SPICase(text)
        self.assertEqual(case.master_name(), 'KaranSharma0445')


    def test_construct_with_no_archive_notice_raises_archive_error(self):
        text = '''
        * {{checkuser|1=DipikaKakar346 }}
        '''
        with self.assertRaises(ArchiveError):
            SPICase(text)


    def test_construct_with_multiple_archive_notices_raises_archive_error(self):
        text = '''
        {{SPIarchive notice|1=Foo}}
        {{SPIarchive notice|1=Bar}}
        '''
        with self.assertRaises(ArchiveError):
            SPICase(text)


    def test_days_returns_iterable_of_case_days(self):
        text = '''
        __TOC__
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===21 March 2019===
        ====Suspected sockpuppets====
        ===22 May 2019===
        ====Suspected sockpuppets====
        ===13 July 2019===
        ====Suspected sockpuppets====
        '''
        case = SPICase(text)
        for d in case.days():
            self.assertIsInstance(d, SPICaseDay)


    def test_find_all_ips(self):
        text1 = '''
        __TOC__
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===21 March 2019===
        ====Suspected sockpuppets====
        {{checkip|1.2.3.6}}

        ===22 May 2019===
        ====Suspected sockpuppets====
        {{checkip|1.2.3.7}}

        ===13 July 2019===
        ====Suspected sockpuppets====
        {{checkip|1.2.3.8}}
        '''

        text2 = '''
        __TOC__
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===1 January 2018===
        ====Suspected sockpuppets====
        {{checkip|1.2.3.4}}
        {{checkip|1.2.3.5}}
        '''

        case = SPICase(make_code(text1), make_code(text2))
        ips = set(case.find_all_ips())
        self.assertEqual(ips, set([
            SPICheckIP('1.2.3.4', '1 January 2018'),
            SPICheckIP('1.2.3.5', '1 January 2018'),
            SPICheckIP('1.2.3.6', '21 March 2019'),
            SPICheckIP('1.2.3.7', '22 May 2019'),
            SPICheckIP('1.2.3.8', '13 July 2019')]))


class SPICaseDayTest(TestCase):
    def test_date_returns_correct_date(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===21 March 2019===
        blah, blah, blaha
        '''
        day = SPICaseDay(make_code(text))
        date = day.date()
        self.assertEqual(date, '21 March 2019')


    def test_day_with_multiple_level_3_headers_raises_archive_error(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===21 March 2019===
        ===22 March 2019===
        blah, blah, blaha
        '''
        day = SPICaseDay(make_code(text))
        with self.assertRaises(ArchiveError):
            day.date()


    def test_day_with_no_level_3_headers_raises_archive_error(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        blah, blah, blaha
        '''
        day = SPICaseDay(make_code(text))
        with self.assertRaises(ArchiveError):
            day.date()


    def test_find_users(self):
        text = '''
        ===21 March 2019===
        {{checkuser|user1}}
        {{checkuser|user2}}
        '''
        day = SPICaseDay(make_code(text))
        users = list(day.find_users())
        self.assertEqual(users, [SPICheckUser('user1', '21 March 2019'),
                                 SPICheckUser('user2', '21 March 2019')])


    def test_find_ips(self):
        text = '''
        ===21 March 2019===
        {{checkip|1.2.3.4}}
        {{checkip|5.6.7.8}}
        '''
        day = SPICaseDay(make_code(text))
        ips = list(day.find_ips())
        self.assertEqual(ips, [SPICheckIP('1.2.3.4', '21 March 2019'),
                               SPICheckIP('5.6.7.8', '21 March 2019')])

