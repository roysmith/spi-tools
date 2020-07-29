from dataclasses import dataclass
from datetime import datetime, timezone
from time import mktime

@dataclass
class Block:
    start: datetime
    end: datetime

    def __init__(self, timestamp, expiry):
        """Timestamp is when the block started, expressed as a struct_time.
        Expiry is when the block ends, either as a struct_time, or the
        string "infinity".

        """
        self.start = datetime.fromtimestamp(mktime(timestamp), tz=timezone.utc)
        if expiry == 'infinity':
            self.end = datetime.replace(datetime.max, tzinfo=timezone.utc)
        else:
            self.end = datetime.fromtimestamp(mktime(expiry), tz=timezone.utc)


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
