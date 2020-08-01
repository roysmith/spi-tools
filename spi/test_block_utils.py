from unittest import TestCase
from datetime import datetime, timezone

from .block_utils import Block, BlockMap, BlockEvent, UnblockEvent


# Note: In all of these tests, it is assumed that the last three
# values of a struct_time (i.e. tm_isdst, tm_zone, and tm_gmtoff) are
# ignored.

max_utc = datetime.replace(datetime.max, tzinfo=timezone.utc)

def _st(year, month, day):
    "Construct a struct_time."
    return (year, month, day, 0, 0, 0, 0, 0, 0)

def _dt(year, month, day):
    "Construct a UTC-aware datetime."
    return datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)


class BlockTest(TestCase):
    def test_construct_indef_block(self):
        block = Block(_st(2020, 2, 7), 'infinity')
        self.assertEqual(block.start, _dt(2020, 2, 7))
        self.assertEqual(block.end, max_utc)

    def test_construct_finite_block(self):
        block = Block(_st(2020, 2, 7), _st(2020, 4, 1))
        self.assertEqual(block.start, _dt(2020, 2, 7))
        self.assertEqual(block.end, _dt(2020, 4, 1))


class BlockMapTest(TestCase):
    def test_construct_empty(self):
        block_map = BlockMap([])
        self.assertEqual(len(block_map.blocks), 0)


    def test_construct_with_one_block(self):
        api_block = {'timestamp': _st(2020, 2, 7),
                     'expiry': _st(2020, 4, 1)}
        block_map = BlockMap([api_block])
        self.assertEqual(len(block_map.blocks), 1)
        self.assertEqual(block_map.blocks[0].start, _dt(2020, 2, 7))
        self.assertEqual(block_map.blocks[0].end, _dt(2020, 4, 1))


    def test_is_blocked_at_time(self):
        api_blocks = [{'timestamp': _st(2020, 2, 7), 'expiry': _st(2020, 4, 1)},
                      {'timestamp': _st(2020, 6, 1), 'expiry': 'infinity'},
                      ]
        block_map = BlockMap(api_blocks)
        self.assertFalse(block_map.is_blocked_at(_dt(2020, 2, 6)))
        self.assertTrue(block_map.is_blocked_at(_dt(2020, 2, 8)))
        self.assertFalse(block_map.is_blocked_at(_dt(2020, 4, 2)))
        self.assertTrue(block_map.is_blocked_at(_dt(2020, 6, 2)))
        self.assertTrue(block_map.is_blocked_at(_dt(3000, 1, 1)))


class BlockEventTest(TestCase):
    def test_construct_finite_block_event(self):
        event = BlockEvent("fred", _dt(2019, 1, 1), _dt(2019, 1, 5))
        self.assertEqual(event.target, "fred")
        self.assertEqual(event.timestamp, _dt(2019, 1, 1))
        self.assertEqual(event.expiry, _dt(2019, 1, 5))
        self.assertFalse(event.is_reblock)


    def test_constuct_indef_block_event(self):
        event = BlockEvent("fred", _dt(2019, 1, 1))
        self.assertEqual(event.target, "fred")
        self.assertEqual(event.timestamp, _dt(2019, 1, 1))
        self.assertIsNone(event.expiry)
        self.assertFalse(event.is_reblock)


    def test_construct_with_expiry_less_than_timestamp_raises_value_error(self):
        with self.assertRaises(ValueError):
            event = BlockEvent("fred", _dt(2019, 1, 1), _dt(2018, 12, 30))


    def test_construct_reblock_event(self):
        event = BlockEvent("fred", _dt(2019, 1, 1), is_reblock=True)
        self.assertEqual(event.target, "fred")
        self.assertEqual(event.timestamp, _dt(2019, 1, 1))
        self.assertIsNone(event.expiry)
        self.assertTrue(event.is_reblock)


    def test_construct_unblock_event(self):
        event = UnblockEvent("fred", _dt(2019, 1, 1))
        self.assertEqual(event.target, "fred")
        self.assertEqual(event.timestamp, _dt(2019, 1, 1))
