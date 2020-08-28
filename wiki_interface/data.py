"Data classes used in various places."


import datetime
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class WikiContrib:
    timestamp: datetime.datetime
    user_name: str
    namespace: int
    title: str
    comment: str
    is_live: bool = True
