from unittest import TestCase
from datetime import datetime, timezone

from wiki_interface.block_utils import BlockEvent, UnblockEvent, UserBlockHistory


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
            BlockEvent("fred", _dt(2019, 1, 1), _dt(2018, 12, 30))


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


class TestUserBlockHistory(TestCase):
    def test_construct_with_no_data(self):
        history = UserBlockHistory([])
        self.assertIsInstance(history, UserBlockHistory)


    def test_construct_with_valid_data(self):
        events = [BlockEvent("fred", _dt(2019, 1, 1)),
                  UnblockEvent("fred", _dt(2019, 1, 2))]
        history = UserBlockHistory(events)
        self.assertEqual(history.events, events)


    def test_construct_with_incorrect_type(self):
        with self.assertRaises(ValueError):
            UserBlockHistory([1])


    def test_construct_with_out_of_order_data(self):
        with self.assertRaises(ValueError):
            UserBlockHistory([BlockEvent("fred", _dt(2019, 1, 3)),
                              BlockEvent("fred", _dt(2019, 1, 2))])


    def test_is_blocked_at_with_indef_block(self):
        events = [BlockEvent("fred", _dt(2019, 1, 1))]
        history = UserBlockHistory(events)

        self.assertTrue(history.is_blocked_at(_dt(2020, 1, 1)))



    def test_is_blocked_at_with_prior_unblock(self):
        history = UserBlockHistory([BlockEvent("fred", _dt(2019, 1, 1)),
                                    UnblockEvent("fred", _dt(2019, 1, 2))])

        self.assertFalse(history.is_blocked_at(_dt(2020, 1, 1)))


    def test_is_blocked_at_with_later_unblock(self):
        history = UserBlockHistory([BlockEvent("fred", _dt(2019, 1, 1)),
                                    UnblockEvent("fred", _dt(2019, 1, 3))])

        self.assertTrue(history.is_blocked_at(_dt(2019, 1, 2)))
