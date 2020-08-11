from unittest import TestCase
from unittest.mock import patch
import textwrap
from ipaddress import IPv4Network
import mwparserfromhell

from .spi_utils import (SpiSourceDocument, SpiCase, SpiCaseDay, SpiIpInfo, SpiUserInfo,
                        ArchiveError, get_current_case_names)
from .wiki_interface import Wiki


def make_code(text):
    return mwparserfromhell.parse(textwrap.dedent(text))

def make_source(text, case_name='whatever'):
    return SpiSourceDocument(case_name, textwrap.dedent(text))


class SpiCaseTest(TestCase):
    def test_master_name_returns_correct_value(self):
        text = '''
        {{SPIarchive notice|1=KaranSharma0445}}
        '''
        case = SpiCase(make_source(text, 'CaseName'))
        self.assertEqual(case.master_name(), 'CaseName')


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
        case = SpiCase(make_source(text))
        for day in case.days():
            self.assertIsInstance(day, SpiCaseDay)


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

        case = SpiCase(make_source(text1, 'CaseName'),
                       make_source(text2, 'CaseName'))
        ips = set(case.find_all_ips())
        self.assertEqual(ips, set([
            SpiIpInfo('1.2.3.4', '1 January 2018', 'CaseName'),
            SpiIpInfo('1.2.3.5', '1 January 2018', 'CaseName'),
            SpiIpInfo('1.2.3.6', '21 March 2019', 'CaseName'),
            SpiIpInfo('1.2.3.7', '22 May 2019', 'CaseName'),
            SpiIpInfo('1.2.3.8', '13 July 2019', 'CaseName')]))


class SpiCaseDayTest(TestCase):
    def test_date_returns_correct_date(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===21 March 2019===
        blah, blah, blaha
        '''
        day = SpiCaseDay(make_code(text), 'title')
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
        day = SpiCaseDay(make_code(text), 'title')
        with self.assertRaises(ArchiveError):
            day.date()


    def test_day_with_no_level_3_headers_raises_archive_error(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        blah, blah, blaha
        '''
        day = SpiCaseDay(make_code(text), 'title')
        with self.assertRaises(ArchiveError):
            day.date()


    def test_find_checkuser_instances(self):
        text = '''
        ===21 March 2019===
        {{checkuser|user1}}
        {{checkuser|user2}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019')])


    def test_find_user_instances(self):
        text = '''
        ===21 March 2019===
        {{user|user1}}
        {{user|user2}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019')])


    def test_find_spi_archive_notice_instances(self):
        text = '''
        ===21 March 2019===
        {{SPIarchive notice|user1}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019')])


    def test_find_user_and_checkuser_instances(self):
        text = '''
        ===21 March 2019===
        {{user|user1}}
        {{checkuser|user2}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019')])


    def test_find_users_skips_mismatched_prefix(self):
        text = '''
        ===21 March 2019===
        {{userfoo|user1}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertEqual(users, [])


    def test_find_users_with_duplicates(self):
        text = '''
        ===21 March 2019===
        {{checkuser|user1}}
        {{checkuser|user1}}
        {{checkuser|user2}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019')])

    def test_find_unique_users(self):
        text = '''
        ===21 March 2019===
        {{checkuser|user1}}
        {{checkuser|user1}}
        {{checkuser|user2}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_unique_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019')])


    def test_find_ips(self):
        text = '''
        ===21 March 2019===
        {{checkip|1.2.3.4}}
        {{checkip|5.6.7.8}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        ips = list(day.find_ips())
        self.assertEqual(ips, [SpiIpInfo('1.2.3.4', '21 March 2019', 'title'),
                               SpiIpInfo('5.6.7.8', '21 March 2019', 'title')])


    def test_find_ips_silently_skips_non_v4_addresses(self):
        text = '''
        ===21 March 2019===
        {{checkip|1.2.3.4}}
        {{checkip|5:6::7}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        ips = list(day.find_ips())
        self.assertEqual(ips, [SpiIpInfo('1.2.3.4', '21 March 2019', 'title')])



class SpiUserInfoTest(TestCase):
    def test_eq(self):
        info1 = SpiUserInfo('user', '1 January 2019')
        info2 = SpiUserInfo('user', '1 January 2019')
        self.assertEqual(info1, info2)


    @staticmethod
    def test_hashable():
        info = SpiUserInfo('user', '1 January 2019')
        hash(info)


class SpiIpInfoTest(TestCase):
    def test_constructor_raises_value_error_if_not_valid_ip_v4_address(self):
        with self.assertRaises(ValueError):
            SpiIpInfo('1:2:3:4::5', '1 January 2019', 'title')


    def test_eq(self):
        info1 = SpiIpInfo('1.2.3.4', '1 January 2019', 'title')
        info2 = SpiIpInfo('1.2.3.4', '1 January 2019', 'title')
        self.assertEqual(info1, info2)


    def test_lt_by_ip(self):
        info1 = SpiIpInfo('1.2.3.4', '1 January 2019', 'title')
        info2 = SpiIpInfo('1.2.3.5', '1 January 2019', 'title')
        self.assertLess(info1, info2)


    def test_lt_by_date(self):
        info1 = SpiIpInfo('1.2.3.4', '1 January 2019', 'title')
        info2 = SpiIpInfo('1.2.3.4', '2 January 2019', 'title')
        self.assertLess(info1, info2)


    @staticmethod
    def test_hashable():
        info = SpiIpInfo('1.2.3.4', '1 January 2019', 'title')
        hash(info)


    def test_find_common_network(self):
        infos = [
            SpiIpInfo('1.2.3.4', '1 January 2019', 'title'),
            SpiIpInfo('1.2.3.17', '1 January 2019', 'title'),
            SpiIpInfo('1.2.3.22', '1 January 2019', 'title'),
            SpiIpInfo('1.2.3.26', '1 January 2019', 'title')]
        network = SpiIpInfo.find_common_network(infos)
        self.assertEqual(network, IPv4Network('1.2.3.0/27'))


class GetCurrentCaseNamesTest(TestCase):
    # pylint: disable=invalid-name

    @patch('spi.wiki_interface.Site')
    def test_no_entries(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = ''

        wiki = Wiki()
        names = get_current_case_names(wiki)

        self.assertEqual(names, [])


    @patch('spi.wiki_interface.Site')
    def test_multiple_entries_with_duplicates(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        {{SPIstatusheader}}
        {{SPIstatusentry|Rajumitwa878|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        {{SPIstatusentry|Trumanshow69|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        '''

        wiki = Wiki()
        names = get_current_case_names(wiki)

        self.assertEqual(set(names), {'Rajumitwa878', 'AntiRacistSwede', 'Trumanshow69'})
