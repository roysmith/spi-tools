from dataclasses import dataclass
from datetime import datetime, timezone
from time import mktime

@dataclass
class Block:
    start: datetime
    end: datetime

    def __init__(self, timestamp, expiry):
        """Api_block is a dict containing at least 'timestamp' and 'expiry'
        keys, as returned by mwclient's site.blocks() method.

        """
        self.start =  datetime.fromtimestamp(mktime(timestamp), tz=timezone.utc)
        if expiry == 'infinity':
            self.end = datetime.replace(datetime.max, tzinfo=timezone.utc)
        else:
            self.end = datetime.fromtimestamp(mktime(expiry), tz=timezone.utc)


@dataclass
class BlockMap:
    def __init__(self, api_blocks):
        self.blocks = [Block(b['timestamp'], b['expiry']) for b in api_blocks]

    def is_blocked_at(self, t):
        "T is a datetime"
        for block in self.blocks:
            if block.start <= t <= block.end:
                return True
        return False
