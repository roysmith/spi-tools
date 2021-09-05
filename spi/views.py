from dataclasses import dataclass
import logging

from django.core.cache import cache

from spi.spi_utils import CacheableSpiCase


logger = logging.getLogger('spi.views')


@dataclass(frozen=True, order=True)
class ValidatedUser:
    username: str
    date: str
    valid: bool


def get_sock_names(wiki, master_name):
    """Returns a iterable over ValidatedUsers

    Discovered usernames are checked for validity.  See
    Wiki.is_valid_username() for what it means to be valid.

    """
    key = f'views.get_sock_names.{master_name}'
    users = cache.get(key)
    if users is None:
        case = CacheableSpiCase.get(wiki, master_name)
        # Need to work out cache invalidation
        usernames = [user_info.username for user_info in case.users]
        valid_usernames = wiki.valid_usernames(usernames)
        users = []
        for user_info in case.users:
            name = user_info.username
            valid = name in valid_usernames
            user = ValidatedUser(name, user_info.date, valid)
            if not valid:
                logger.warning('invalid username (%s) in case "%s"', user, master_name)
            users.append(user)
        cache.set(key, users, 300)
    return users
