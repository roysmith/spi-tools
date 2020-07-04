from unittest import TestCase
from spi.views import SockSelectView
from spi.spi_utils import SpiUserInfo

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

