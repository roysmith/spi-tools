"Data classes used in various places."


import datetime
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True, order=True)
class WikiContrib:
    '''If the comment is hidden
    (https://en.wikipedia.org/wiki/Wikipedia:Revision_deletion) the
    comment attribute will be None.  Note, if a revision simply has no
    comment, the comment attribute will be the empty string.

    '''
    rev_id: int
    timestamp: datetime.datetime
    user_name: str
    namespace: int
    title: str
    comment: str
    is_live: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LogEvent:
    timestamp: datetime.datetime
    user_name: str
    title: str
    type: str
    action: str
    comment: str
