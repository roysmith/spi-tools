from datetime import datetime, timezone
from time import mktime

def struct_to_datetime(struct_time):
    """Convert a struct_time to a UTC aware datetime.

    """
    return datetime.fromtimestamp(mktime(struct_time), tz=timezone.utc)
