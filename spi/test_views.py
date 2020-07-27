from unittest import TestCase
from .views import SockSelectView, UserSummary
from .spi_utils import SpiUserInfo

class SockSelectViewTest(TestCase):
    def test_build_context(self):
        case_name = "Foo"
        user_infos = [SpiUserInfo("User1", "20 June 2020"),
                      SpiUserInfo("User2", "21 June 2020")]

        context = SockSelectView.build_context(case_name, user_infos)

        self.assertEqual(context['case_name'], "Foo")
        expected_items = {('User1', 'User1', '20 June 2020'),
                          ('User2', 'User2', '21 June 2020')}
        items = {(field.label, name, date)
                 for field, name, date in context['form_info']}
        self.assertEqual(items, expected_items)


    def test_build_context_deduplicates_users(self):
        case_name = "Foo"
        user_infos = [SpiUserInfo("User1", "20 June 2020"),
                      SpiUserInfo("User1", "20 June 2020"),
                      SpiUserInfo("User2", "21 June 2020")]

        context = SockSelectView.build_context(case_name, user_infos)

        self.assertEqual(context['case_name'], "Foo")
        expected_items = {('User1', 'User1', '20 June 2020'),
                          ('User2', 'User2', '21 June 2020')}
        items = {(field.label, name, date)
                 for field, name, date in context['form_info']}
        self.assertEqual(items, expected_items)


class UserSummaryTest(TestCase):
    def test_urlencoded_username(self):
        summary = UserSummary('foo', '20 July 2020')
        self.assertEqual(summary.username, 'foo')
        self.assertEqual(summary.urlencoded_username(), 'foo')

    def test_urlencoded_username_with_slash(self):
        summary = UserSummary('foo/bar', '20 July 2020')
        self.assertEqual(summary.username, 'foo/bar')
        self.assertEqual(summary.urlencoded_username(), 'foo%2Fbar')
