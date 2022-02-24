from unittest import TestCase
from unittest.mock import patch, call, NonCallableMock
from textwrap import dedent
from ipaddress import IPv4Network
from datetime import datetime
import mwparserfromhell

from wiki_interface import Wiki
from wiki_interface.data import WikiContrib
from spi.spi_utils import (SpiSourceDocument, SpiCase, SpiCaseDay, SpiIpInfo, SpiUserInfo, CacheableSpiCase,
                           ArchiveError, get_current_case_names, _find_active_case_template)


def make_code(text):
    return mwparserfromhell.parse(dedent(text))

def make_source(text, case_name='whatever'):
    return SpiSourceDocument(case_name, dedent(text))


class CacheableSpiCaseTest(TestCase):
    @patch('spi.spi_utils.cache')
    def test_construct(self, cache):
        case = CacheableSpiCase('Fred')

        cache.get.assert_not_called()
        cache.set.assert_not_called()
        self.assertEqual(case.master_name, 'Fred')


    @patch('spi.spi_utils.cache')
    def test_get_with_empty_cache_and_empty_case(self, cache):
        wiki = NonCallableMock(Wiki)
        wiki.page().revisions.side_effect = [
            [WikiContrib(2020_07_29, datetime(2020, 7, 29), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred', '')],
            [WikiContrib(2020_07_28, datetime(2020, 7, 28), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred/Archive', '')],
        ]
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                '''),
            dedent(
                '''
                ''')]
        cache.get.return_value = None
        wiki.page.reset_mock()

        case = CacheableSpiCase.get(wiki, 'Fred')

        expected_case = CacheableSpiCase('Fred',
                                         2020_07_29,
                                         [SpiUserInfo('Fred', None)],
                                         [])
        self.assertEqual(wiki.page.call_args_list, [
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
        ])
        cache.get.assert_called_once_with('spi.CacheableSpiCase.Fred', version=2020_07_29)
        cache.set.assert_called_once_with('spi.CacheableSpiCase.Fred', expected_case, version=2020_07_29)
        self.assertEqual(case, expected_case)


    @patch('spi.spi_utils.cache')
    def test_rev_id_is_populated_with_latest_id_from_current_page(self, cache):
        wiki = NonCallableMock(Wiki)
        wiki.page().revisions.side_effect = [
            [WikiContrib(2020_07_29, datetime(2020, 7, 29), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred', '')],
            [WikiContrib(2020_07_28, datetime(2020, 7, 28), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred/Archive', '')],
        ]
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                '''),
            dedent(
                '''
                ''')]
        cache.get.return_value = None
        wiki.page.reset_mock()

        case = CacheableSpiCase.get(wiki, 'Fred')

        expected_case = CacheableSpiCase('Fred',
                                         2020_07_29,
                                         [SpiUserInfo('Fred', None)],
                                         [])
        self.assertEqual(wiki.page.call_args_list, [
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
            ])
        cache.get.assert_called_once_with('spi.CacheableSpiCase.Fred', version=2020_07_29)
        cache.set.assert_called_once_with('spi.CacheableSpiCase.Fred', expected_case, version=2020_07_29)
        self.assertEqual(case.rev_id, 2020_07_29)


    @patch('spi.spi_utils.cache')
    def test_rev_id_is_populated_with_latest_id_from_archive(self, cache):
        wiki = NonCallableMock(Wiki)
        wiki.page().revisions.side_effect = [
            [WikiContrib(2020_07_29, datetime(2020, 7, 29), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred', '')],
            [WikiContrib(2020_07_30, datetime(2020, 7, 30), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred/Archive', '')],
        ]
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                '''),
            dedent(
                '''
                ''')]
        cache.get.return_value = None
        wiki.page.reset_mock()

        case = CacheableSpiCase.get(wiki, 'Fred')

        expected_case = CacheableSpiCase('Fred',
                                         2020_07_30,
                                         [SpiUserInfo('Fred', None)],
                                         [])
        self.assertEqual(wiki.page.call_args_list, [
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
            ])
        cache.get.assert_called_once_with('spi.CacheableSpiCase.Fred', version=2020_07_30)
        cache.set.assert_called_once_with('spi.CacheableSpiCase.Fred', expected_case, version=2020_07_30)
        self.assertEqual(case.rev_id, 2020_07_30)


    @patch('spi.spi_utils.cache')
    def test_rev_id_is_populated_with_current_page_id_if_archive_is_missing(self, cache):
        wiki = NonCallableMock(Wiki)
        wiki.page().revisions.side_effect = [
            [WikiContrib(2020_07_29, datetime(2020, 7, 29), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred', '')],
            [],
        ]
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                '''),
            dedent(
                '''
                ''')]
        cache.get.return_value = None
        wiki.page.reset_mock()

        case = CacheableSpiCase.get(wiki, 'Fred')

        expected_case = CacheableSpiCase('Fred',
                                         2020_07_29,
                                         [SpiUserInfo('Fred', None)],
                                         [])
        self.assertEqual(wiki.page.call_args_list, [
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
        ])
        cache.get.assert_called_once_with('spi.CacheableSpiCase.Fred', version=2020_07_29)
        cache.set.assert_called_once_with('spi.CacheableSpiCase.Fred', expected_case, version=2020_07_29)
        self.assertEqual(case.rev_id, 2020_07_29)


    @patch('spi.spi_utils.cache')
    def test_cached_value_is_used_if_version_matches(self, cache):
        wiki = NonCallableMock(Wiki)
        wiki.page().revisions.side_effect = [
            [WikiContrib(2020_07_29, datetime(2020, 7, 29), 'user1', 4, 'Wikipedia:Sockpuppet investigations/Fred', '')],
            [],
        ]
        cache.get.return_value = CacheableSpiCase('Fred', 2020_07_29)
        wiki.page.reset_mock()
        cache.reset_mock()

        case = CacheableSpiCase.get(wiki, 'Fred')

        self.assertEqual(wiki.page.call_args_list, [
            call('Wikipedia:Sockpuppet investigations/Fred'),
            call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
        ])
        cache.get.assert_called_once_with('spi.CacheableSpiCase.Fred', version=2020_07_29)
        cache.set.assert_not_called()
        self.assertEqual(case.rev_id, 2020_07_29)


class SpiCaseTest(TestCase):
    def test_for_master_with_no_data(self):
        wiki = NonCallableMock(Wiki)
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                '''),
            dedent(
                '''
                ''')]
        wiki.reset_mock()

        case = SpiCase.for_master(wiki, 'Fred')

        self.assertEqual(wiki.page.call_args_list,
                         [call('Wikipedia:Sockpuppet investigations/Fred'),
                          call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
                         ])
        self.assertEqual(case.master_name, 'Fred')
        self.assertEqual(list(case.days()), [])
        self.assertEqual(list(case.find_all_ips()), [])
        self.assertEqual(list(case.find_all_users()), [SpiUserInfo('Fred', None)])


    def test_for_master_with_multiple_days(self):
        wiki = NonCallableMock(Wiki)
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                ===21 March 2019===
                {{checkuser|user1}}
                {{checkuser|user2}}
                ===22 March 2019===
                {{checkuser|user3}}
                {{checkuser|user4}}

                '''),
            dedent(
                '''
                ''')]
        wiki.reset_mock()

        case = SpiCase.for_master(wiki, 'Fred')

        self.assertEqual(wiki.page.call_args_list,
                         [call('Wikipedia:Sockpuppet investigations/Fred'),
                          call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
                         ])
        self.assertEqual(case.master_name, 'Fred')
        self.assertEqual(list(case.find_all_ips()), [])
        self.assertEqual(list(case.find_all_users()),
                         [SpiUserInfo('Fred', None),
                          SpiUserInfo('user1', '21 March 2019'),
                          SpiUserInfo('user2', '21 March 2019'),
                          SpiUserInfo('user3', '22 March 2019'),
                          SpiUserInfo('user4', '22 March 2019'),
                         ])


    def test_for_master_with_multiple_days_and_mixed_new_and_old_style_headers(self):
        wiki = NonCallableMock(Wiki)
        wiki.page().text.side_effect = [
            dedent(
                '''
                {{SPIarchive notice|1=Fred}}
                =====<big>21 March 2019</big>=====
                {{checkuser|user1}}
                {{checkuser|user2}}
                ===22 March 2019===
                {{checkuser|user3}}
                {{checkuser|user4}}

                '''),
            dedent(
                '''
                ''')]
        wiki.reset_mock()

        case = SpiCase.for_master(wiki, 'Fred')

        self.assertEqual(wiki.page.call_args_list,
                         [call('Wikipedia:Sockpuppet investigations/Fred'),
                          call('Wikipedia:Sockpuppet investigations/Fred/Archive'),
                         ])
        self.assertEqual(case.master_name, 'Fred')
        self.assertEqual(list(case.find_all_ips()), [])
        self.assertEqual(list(case.find_all_users()),
                         [SpiUserInfo('Fred', None),
                          SpiUserInfo('user1', '21 March 2019'),
                          SpiUserInfo('user2', '21 March 2019'),
                          SpiUserInfo('user3', '22 March 2019'),
                          SpiUserInfo('user4', '22 March 2019'),
                         ])


    def test_constructor_handles_old_style_headers(self):
        text = '''
        __TOC__
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        =====<big>22 May 2011</big>=====
        ;Suspected sockpuppets
        '''
        case = SpiCase(make_source(text))
        dates = [day.date() for day in case.days()]
        self.assertEqual(dates, ['22 May 2011'])


    def test_constructor_handles_mix_of_new_and_old_style_headers(self):
        text = '''
        __TOC__
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        =====<big>22 May 2011</big>=====
        ===22 May 2020===
        =====<big>22 May 2012</big>=====
        ===22 May 2021===
        '''
        case = SpiCase(make_source(text))
        dates = [day.date() for day in case.days()]
        self.assertEqual(dates, ['22 May 2011', '22 May 2020', '22 May 2012', '22 May 2021'])


    def test_master_name_returns_correct_value(self):
        text = '''
        {{SPIarchive notice|1=KaranSharma0445}}
        '''
        case = SpiCase(make_source(text, 'CaseName'))
        self.assertEqual(case.master_name, 'CaseName')


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


    def test_find_all_ips_with_no_data(self):
        text = '''
        {{SPIarchive notice|Maung Ko Htet}}
        '''
        case = SpiCase(make_source(text, 'Maung Ko Htet'))

        infos = case.find_all_ips()

        self.assertEqual(list(infos), [])


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


    def test_date_trims_leading_and_trailing_whitespace(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        === 21 March 2019 ===
        blah, blah, blaha
        '''
        day = SpiCaseDay(make_code(text), 'title')
        date = day.date()
        self.assertEqual(date, '21 March 2019')


    def test_day_with_multiple_level_3_headers_raises_archive_error_with_header_text(self):
        text = '''
        {{SPIarchive notice|1=Crazyalien}}
        {{SPIpriorcases}}
        ===21 March 2019===
        ===22 March 2019===
        blah, blah, blaha
        '''
        day = SpiCaseDay(make_code(text), 'title')
        with self.assertRaisesRegex(ArchiveError, r"('21 March 2019', '22 March 2019')"):
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


    def test_find_users_includes_checkip_templates(self):
        text = '''
        ===21 March 2019===
        {{checkuser|user1}}
        {{checkuser|user2}}
        {{checkip|1.2.3.4}}
        {{checkIP|5.6.7.8}}

        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019'),
                                      SpiUserInfo('1.2.3.4', '21 March 2019'),
                                      SpiUserInfo('5.6.7.8', '21 March 2019'),
        ])

    def test_find_user_includes_socklist_templates(self):
        text = '''
        ===21 March 2019===
        {{checkuser|user1}}
        {{checkip|1.2.3.4}}
        {{socklist|user2}}

        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertCountEqual(users, [SpiUserInfo('user1', '21 March 2019'),
                                      SpiUserInfo('user2', '21 March 2019'),
                                      SpiUserInfo('1.2.3.4', '21 March 2019'),
        ])


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


    def test_find_ips_accepts_uppercase_variants(self):
        text = '''
        ===21 March 2019===
        {{checkip|1.2.3.4}}
        {{checkIP|5.6.7.8}}
        {{Checkip|9.10.11.12}}
        {{CheckIP|13.14.15.16}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        ips = list(day.find_ips())
        self.assertCountEqual(ips, [
            SpiIpInfo('1.2.3.4', '21 March 2019', 'title'),
            SpiIpInfo('5.6.7.8', '21 March 2019', 'title'),
            SpiIpInfo('9.10.11.12', '21 March 2019', 'title'),
            SpiIpInfo('13.14.15.16', '21 March 2019', 'title'),
        ])


    def test_find_ips_uses_socklist_templates(self):
        text = '''
        ===21 March 2019===
        {{checkip|1.2.3.4}}
        {{socklist|5.6.7.8}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        ips = list(day.find_ips())
        self.assertCountEqual(ips, [
            SpiIpInfo('1.2.3.4', '21 March 2019', 'title'),
            SpiIpInfo('5.6.7.8', '21 March 2019', 'title'),
        ])



    def test_parse_socklist_with_no_arguments_yields_no_users(self):
        text = '''
        ===21 March 2019===
        {{sock list}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.parse_socklist())
        self.assertEqual(users, [])


    def test_parse_socklist_ignores_named_arguments(self):
        text = '''
        ===21 March 2019===
        {{sock list|foo|bar=baz}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.parse_socklist())
        self.assertEqual(users, ['foo'])


    def test_parse_socklist_with_n_arguments_yields_n_users(self):
        text = '''
        ===21 March 2019===
        {{sock list|foo|bar|baz}}
        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.parse_socklist())
        self.assertEqual(users, ['foo', 'bar', 'baz'])


    def test_socklist_parameters_with_no_names_are_recognized_as_uses(self):
        text = '''
        ===23 February 2022===
        {{SPI case status|close}}
        ====Suspected sockpuppets====
        {{sock list|user1|user2}}

        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertEqual(users, [SpiUserInfo('user1', '23 February 2022'),
                                 SpiUserInfo('user2', '23 February 2022')])


    def test_socklist_parameters_with_numeric_names_are_recognized_as_users(self):
        text = '''
        ===23 February 2022===
        {{SPI case status|close}}
        ====Suspected sockpuppets====
        {{sock list|1=user1|2=user2}}

        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertEqual(users, [SpiUserInfo('user1', '23 February 2022'),
                                 SpiUserInfo('user2', '23 February 2022')])



    def test_socklist_parameters_with_mixed_numeric_names_and_no_names_are_recognized_as_users(self):
        text = '''
        ===23 February 2022===
        {{SPI case status|close}}
        ====Suspected sockpuppets====
        {{sock list|1=user1|user2}}

        '''
        day = SpiCaseDay(make_code(text), 'title')
        users = list(day.find_users())
        self.assertEqual(users, [SpiUserInfo('user1', '23 February 2022'),
                                 SpiUserInfo('user2', '23 February 2022')])


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

    @patch('wiki_interface.wiki.Site')
    @patch('spi.spi_utils._find_active_case_template')
    def test_no_entries(self, mock__find_active_case_template, mock_Site):
        mock__find_active_case_template.return_value = 'whatever'
        mock_Site().pages.__getitem__().text.return_value = ''

        wiki = Wiki()
        names = get_current_case_names(wiki)

        self.assertEqual(names, [])
        mock_Site().pages.__getitem__().text.assert_called_once_with()


    @patch('wiki_interface.wiki.Site')
    @patch('spi.spi_utils._find_active_case_template')
    def test_multiple_entries_with_duplicates(self, mock__find_active_case_template, mock_Site):
        mock__find_active_case_template.return_value = 'whatever'
        mock_Site().pages.__getitem__().text.return_value = '''
        {{SPIstatusheader}}
        {{SPIstatusentry|Rajumitwa878|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        {{SPIstatusentry|Trumanshow69|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        '''

        wiki = Wiki()
        names = get_current_case_names(wiki)

        self.assertCountEqual(names, ['Rajumitwa878', 'AntiRacistSwede', 'Trumanshow69'])
        mock_Site().pages.__getitem__().text.assert_called_once_with()


    @patch('wiki_interface.wiki.Site')
    @patch('spi.spi_utils._find_active_case_template')
    def test_case_name_with_slash(self, mock__find_active_case_template, mock_Site):
        mock__find_active_case_template.return_value = 'whatever'
        mock_Site().pages.__getitem__().text.return_value = '''
        {{SPIstatusheader}}
        {{SPIstatusentry|Rajumitwa878|--|--|--|--|--|--}}
        {{SPIstatusentry|AntiRacistSwede|--|--|--|--|--|--}}
        {{SPIstatusentry|2605:E000:1F00:D3F1:0:0:0:0/64|--|--|--|--|--|--}}
        '''

        wiki = Wiki()
        names = get_current_case_names(wiki)

        self.assertEqual(set(names), {'Rajumitwa878', 'AntiRacistSwede'})
        mock_Site().pages.__getitem__().text.assert_called_once_with()


class FindActiveCaseTemplateTest(TestCase):
    # pylint: disable=invalid-name

    @patch('wiki_interface.wiki.Site')
    def test_overview(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        <h2> Cases currently listed at SPI </h2>
        {{purge box}}
        {{Wikipedia:Sockpuppet investigations/Cases/Overview}}
        <!-- This can be used as a backup: {{User:AmandaNP/SPI case list}} -->
        '''

        wiki = Wiki()
        template = _find_active_case_template(wiki)
        self.assertEqual(template, 'Wikipedia:Sockpuppet investigations/Cases/Overview')


    @patch('wiki_interface.wiki.Site')
    def test_amanda(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        <h2> Cases currently listed at SPI </h2>
        {{purge box}}
        <!-- Switching to backup. {{Wikipedia:Sockpuppet investigations/Cases/Overview}}-->
        {{User:AmandaNP/SPI case list}}
        |}
        '''

        wiki = Wiki()
        template = _find_active_case_template(wiki)
        self.assertEqual(template, 'User:AmandaNP/SPI case list')


    @patch('wiki_interface.wiki.Site')
    def test_mz7(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        <h2> Cases currently listed at SPI </h2>
        {{purge box}}
        <!-- Switching to backup for the time being, main case list at {{Wikipedia:Sockpuppet investigations/Cases/Overview}} -->
        {{User:Mz7/SPI case list}} <!-- Mz7's backup list more closely emulates the "normal" table. The original backup with some hacky table-code to get it working: 
        {|class="wikitable sortable" width="100%"
        !Investigation!!Status!!Filer!!Date filed!!Last user edit!!timestamp!!Last clerk/CU edit
        {{User:AmandaNP/SPI case list}}
        |}
        -->
        '''

        wiki = Wiki()
        template = _find_active_case_template(wiki)
        self.assertEqual(template, 'User:Mz7/SPI case list')


    @patch('wiki_interface.wiki.Site')
    def test_None(self, mock_Site):
        mock_Site().pages.__getitem__().text.return_value = '''
        <h2> Cases currently listed at SPI </h2>
        {{purge box}}
        <!-- Switching to backup. {{Wikipedia:Sockpuppet investigations/Cases/Overview}}-->
        <!-- {{User:AmandaNP/SPI case list}} -->
        |}
        '''

        wiki = Wiki()
        template = _find_active_case_template(wiki)
        self.assertIsNone(template)
