from unittest import TestCase
import time
import datetime

from .time_utils import struct_to_datetime

class StructToDatetimeTest(TestCase):
    def test_convert(self):
        self.assertEqual(struct_to_datetime(time.struct_time((2001, 1, 2, 0, 0, 0, 0, 0, 0))),
                         datetime.datetime(2001, 1, 2, tzinfo=datetime.timezone.utc))
