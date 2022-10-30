from unittest import TestCase
from unittest.mock import patch
from tools_app import git


@patch('tools_app.git.sh', spec=['git'])
class GetStatusTest(TestCase):
    def test_clean_repo_returns_dirty_equal_false(self, mock_sh):
        mock_sh.git.return_value = [
            '# branch.oid 6606c459dd972a1e8907839c6775ae1cd30ce840\n',
            '# branch.head dev\n',
            '# branch.upstream origin/dev\n',
            '# branch.ab +0 -0\n',
        ]
        data, dirty = git.get_status()
        self.assertEqual(data['branch.head'], 'dev')
        self.assertEqual(data['branch.oid'], '6606c459dd972a1e8907839c6775ae1cd30ce840')
        self.assertFalse(dirty)

    def test_dirty_repo_returns_dirty_equal_true(self, mock_sh):
        mock_sh.git.return_value = [
            '# branch.oid 6606c459dd972a1e8907839c6775ae1cd30ce840\n',
            '# branch.head dev\n',
            '# branch.upstream origin/dev\n',
            '# branch.ab +0 -0\n',
            '? git.py\n',
            '? test_git.p\n',
        ]
        data, dirty = git.get_status()
        self.assertEqual(data['branch.head'], 'dev')
        self.assertEqual(data['branch.oid'], '6606c459dd972a1e8907839c6775ae1cd30ce840')
        self.assertTrue(dirty)


@patch('tools_app.git.sh', spec=['git'])
class GetTagsTest(TestCase):
    def test_no_tags_returns_empty_list(self, mock_sh):
        mock_sh.git.return_value = []
        tags = git.get_tags('foo')
        self.assertEqual(tags, [])


    def test_one_tags_returns_list_of_one_string(self, mock_sh):
        mock_sh.git.return_value = [
            'tag1\n',
        ]
        tags = git.get_tags('foo')
        self.assertEqual(tags, ['tag1'])


    def test_multiple_tags_returns_list_of_strings(self, mock_sh):
        mock_sh.git.return_value = [
            'tag1\n',
            'tag2\n',
            'tag3\n',
        ]
        tags = git.get_tags('foo')
        self.assertEqual(tags, ['tag1', 'tag2', 'tag3'])


@patch('tools_app.git.get_status', autospec=True)
@patch('tools_app.git.get_tags', autospec=True)
class GetInfoTest(TestCase):
    def test_clean_repo_no_tags(self, mock_get_tags, mock_get_status):
        mock_get_tags.return_value = []
        mock_get_status.return_value = ({'branch.oid': 'oid',
                                         'branch.head': 'branch'},
                                        False)
        self.assertEqual(git.get_info(), 'branch (oid)')


    def test_dirty_repo_with_one_tag(self, mock_get_tags, mock_get_status):
        mock_get_tags.return_value = ['tag']
        mock_get_status.return_value = ({'branch.oid': 'oid',
                                         'branch.head': 'branch'},
                                        True)
        self.assertEqual(git.get_info(), 'branch (oid+ [tag])')


    def test_dirty_repo_with_multiple_tags(self, mock_get_tags, mock_get_status):
        mock_get_tags.return_value = ['tag1', 'tag2', 'tag3']
        mock_get_status.return_value = ({'branch.oid': 'oid',
                                         'branch.head': 'branch'},
                                        True)
        self.assertEqual(git.get_info(), 'branch (oid+ [tag1, tag2, tag3])')
