"Data classes used in various places."


import datetime
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class WikiContrib:
    '''If the comment is hidden
    (https://en.wikipedia.org/wiki/Wikipedia:Revision_deletion) the
    comment attribute will be None.  Note, if a revision simply has no
    comment, the comment attribute will be the empty string.

    '''
    timestamp: datetime.datetime
    user_name: str
    namespace: int
    title: str
    comment: str
    is_live: bool = True
