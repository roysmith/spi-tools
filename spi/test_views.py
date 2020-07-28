from unittest import TestCase
from unittest.mock import patch, MagicMock

from django.test import Client

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


class SockInfoViewTest(TestCase):
    @patch('mwclient.Site', new_callable=MagicMock, spec=['pages', 'users'])
    def test_get_with_empty_mw_queries_renders_one_summary(self, mock_Site):
        mock_site = mock_Site()
        mock_site.pages.__getitem__().text.return_value = ''
        mock_site.users().return_value = iter([{}])
        client = Client()
        response = client.get('/spi/spi-sock-info/Foo/')
        self.assertIn('spi/sock-info.dtl', [t.name for t in response.templates])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['case_name'], 'Foo')
        self.assertEqual(response.context['summaries'], [UserSummary('Foo', None)])
