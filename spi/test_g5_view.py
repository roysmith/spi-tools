from unittest.mock import patch

from spi.test_spi_view import ViewTestCase
from spi.spi_view import ValidatedUser


class G5ViewTest(ViewTestCase):
    #pylint: disable=arguments-differ
    def setUp(self):
        super().setUp('spi.g5_view')


    @patch('spi.g5_view.get_sock_names', autospec=True)
    def test_view_returns_200(self, mock_get_sock_names):
        self.mock_wiki.page_exists.return_value = True
        self.mock_wiki.page.return_value.revisions.return_value = {'rev_id': 1}
        mock_get_sock_names.return_value = [ValidatedUser("User1", "20 June 2020", True),
                                            ValidatedUser("User2", "21 June 2020", True),
                                            ValidatedUser("User3", "21 June 2020", False)]

        response = self.client.get('/spi/g5/Fred')

        self.assertEqual(response.status_code, 200)
