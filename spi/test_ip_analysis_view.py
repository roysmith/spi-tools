from unittest.mock import patch

from spi.test_spi_view import ViewTestCase

# pylint: disable=invalid-name
# pylint: disable=duplicate-code
class IpAnalysisiewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('spi.ip_analysis_view')


    @patch('spi.ip_analysis_view.CacheableSpiCase', autospec=True)
    def test_view_returns_200(self, mock_CacheableSpiCase):
        self.mock_wiki.page_exists.return_value = True
        self.mock_wiki.page.return_value.revisions.return_value = {'rev_id': 1}
        mock_CacheableSpiCase.get.return_value.ip_addresses = []

        response = self.client.get('/spi/ip-analysis/Ferd/')

        self.assertEqual(response.status_code, 200)
