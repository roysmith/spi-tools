from time import struct_time
from unittest import TestCase
from block_utils import Block, BlockMap
from datetime import datetime, timezone


# Note: In all of these tests, it is assumed that the last three
# values of a struct_time (i.e. tm_isdst, tm_zone, and tm_gmtoff) are
# ignored.

max_utc = datetime.replace(datetime.max, tzinfo=timezone.utc)

def st(year, month, day):
    "Construct a struct_time."
    return (year, month, day, 0, 0, 0, 0, 0, 0)

def dt(year, month, day):
    "Construct a UTC-aware datetime."
    return datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)


class BlockTest(TestCase):
    def test_construct_indef_block(self):
        block = Block(st(2020, 2, 7), 'infinity')
        self.assertEqual(block.start, dt(2020, 2, 7))
        self.assertEqual(block.end, max_utc)

    def test_construct_finite_block(self):
        block = Block(st(2020, 2, 7), st(2020, 4, 1))
        self.assertEqual(block.start, dt(2020, 2, 7))
        self.assertEqual(block.end, dt(2020, 4, 1))


class BlockMapTest(TestCase):
    def test_construct_empty(self):
        map = BlockMap([])
        self.assertEqual(len(map.blocks), 0)


    def test_construct_with_one_block(self):
        api_block = {'timestamp': st(2020, 2, 7),
                     'expiry': st(2020, 4, 1),
        }
        map = BlockMap([api_block])
        self.assertEqual(len(map.blocks), 1)
        self.assertEqual(map.blocks[0].start, dt(2020, 2, 7))
        self.assertEqual(map.blocks[0].end, dt(2020, 4, 1))


    def test_is_blocked_at_time(self):
        api_blocks = [{'timestamp': st(2020, 2, 7), 'expiry': st(2020, 4, 1)},
                      {'timestamp': st(2020, 6, 1), 'expiry': 'infinity'},
                      ]
        map = BlockMap(api_blocks)
        self.assertFalse(map.is_blocked_at(dt(2020, 2, 6)))
        self.assertTrue(map.is_blocked_at(dt(2020, 2, 8)))
        self.assertFalse(map.is_blocked_at(dt(2020, 4, 2)))
        self.assertTrue(map.is_blocked_at(dt(2020, 6, 2)))
        self.assertTrue(map.is_blocked_at(dt(3000, 1, 1)))
