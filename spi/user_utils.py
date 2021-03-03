from dataclasses import dataclass, field
from typing import List
from itertools import chain
import logging

from django.core.cache import cache

from wiki_interface import WikiContrib


logger = logging.getLogger('spi.views')


@dataclass(frozen=True)
class CacheableUserContribs:
    data: List[WikiContrib] = field(default_factory=list)


    def get(wiki, user_name):
        key = f'spi.CacheableUserContribs.{user_name}'
        data = cache.get(key, default=[])
        logger.info('got %d from cache (%s)', len(data), key)
        end_time = data[0].timestamp.isoformat() if data else None
        new_data = list(wiki.user_contributions(user_name, end=end_time))
        if new_data:
            logger.info('got %d new for %s', len(new_data), key)
            if data and new_data[-1].rev_id == data[0].rev_id:
                logger.info('pop')
                new_data.pop()
        if new_data:
            data = list(chain(new_data, data))
            logger.info('setting %s in cache (%d entries)', key, len(data))
            cache.set(key, data)
        return CacheableUserContribs(data)
