from typing import List
from dataclasses import dataclass
from datetime import datetime, timezone

from .time_utils import struct_to_datetime

utc_min = datetime.replace(datetime.min, tzinfo=timezone.utc)
utc_max = datetime.replace(datetime.max, tzinfo=timezone.utc)


@dataclass
class Block:
    start: datetime
    end: datetime

    def __init__(self, timestamp, expiry):
        """Timestamp is when the block started, expressed as a struct_time.
        Expiry is when the block ends, either as a struct_time, or the
        string "infinity".

        """
        self.start = struct_to_datetime(timestamp)
        if expiry == 'infinity':
            self.end = utc_max
        else:
            self.end = struct_to_datetime(expiry)


@dataclass
class BlockMap:
    def __init__(self, api_blocks):
        self.blocks = [Block(b['timestamp'], b['expiry']) for b in api_blocks]

    def is_blocked_at(self, timestamp):
        "Timestamp is a datetime"
        for block in self.blocks:
            if block.start <= timestamp <= block.end:
                return True
        return False


@dataclass(frozen=True)
class BaseBlockEvent:
    pass


@dataclass(frozen=True)
class BlockEvent(BaseBlockEvent):
    """A log event of type block/block or block/reblock.

    Target is the user who is blocked (called "title" in the logs).
    Note: the target field does not include the leading "User:".

    For an indef block, expiry will be None.  If an expiry is given,
    raises ValueError if expiry < timestamp.

    """
    target: str
    timestamp: datetime
    expiry: datetime = None
    is_reblock: bool = False

    def __post_init__(self):
        if self.expiry and self.expiry < self.timestamp:
            raise ValueError(f'expiry ({self.expiry}) > timestamp({self.timestamp})')


@dataclass(frozen=True)
class UnblockEvent(BaseBlockEvent):
    """A log event of type block/unblock.

    Target is the user who is blocked (called "title" in the logs).
    Note: the target field does not include the leading "User:".

    """
    target: str
    timestamp: datetime


@dataclass(frozen=True)
class UserBlockHistory:
    """A representation of a user's block log.

    Constructor takes a list of BlockEvents and/or UnblockEvents,
    sorted in strictly increasing order of timestamp.  Raises
    ValueError is they're out of order or not one of those classes.

    """
    events: List[BaseBlockEvent]


    def __post_init__(self):
        previous_timestamp = utc_min
        for event in self.events:
            if not isinstance(event, (BlockEvent, UnblockEvent)):
                raise ValueError(f'wrong type: {event}')
            if event.timestamp <= previous_timestamp:
                raise ValueError(f'event out of order: {event}')
            previous_timestamp = event.timestamp


    def is_blocked_at(self, timestamp):
        """Determine if the user was blocked at a specific point in time.

        Returns True if they were, False otherwise.

        """
        is_blocked = False
        for event in self.events:
            if event.timestamp > timestamp:
                break
            is_blocked = isinstance(event, BlockEvent)
        return is_blocked
