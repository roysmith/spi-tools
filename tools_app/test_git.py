from unittest import TestCase
import git


class ParseOutputTest(TestCase):
    def test_clean_repo(self):
        output = ['# branch.oid 6606c459dd972a1e8907839c6775ae1cd30ce840\n',
                  '# branch.head dev\n',
                  '# branch.upstream origin/dev\n',
                  '# branch.ab +0 -0\n',
        ]
        expected_result = 'dev (6606c459dd972a1e8907839c6775ae1cd30ce840)'
        result = git.parse_output(output)
        self.assertEqual(result, expected_result)

    def test_dirty_repo(self):
        output = ['# branch.oid 6606c459dd972a1e8907839c6775ae1cd30ce840\n',
                  '# branch.head dev\n',
                  '# branch.upstream origin/dev\n',
                  '# branch.ab +0 -0\n',
                  '? git.py\n',
                  '? test_git.p\n',
        ]
        expected_result = 'dev (6606c459dd972a1e8907839c6775ae1cd30ce840+)'
        result = git.parse_output(output)
        self.assertEqual(result, expected_result)

        
