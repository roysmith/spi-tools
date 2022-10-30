from dataclasses import dataclass
from enum import IntEnum
import logging
import re

from django.views import View

from spi import icache as cache
from spi.spi_utils import CacheableSpiCase
from wiki_interface import Wiki


logger = logging.getLogger('spi.views')


class SockType(IntEnum):
    NONE = 0
    SUSPECTED = 1
    KNOWN = 2  # proven or confirmed


@dataclass(frozen=True, order=True)
class ValidatedUser:
    username: str
    date: str
    valid: bool
    sock_type: SockType = SockType.NONE


class SpiView(View):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.wiki = Wiki(request)


def get_sock_names(wiki, master_name):
    """Returns a iterable over ValidatedUsers

    Discovered usernames are checked for validity.  See
    Wiki.validate_username() for what it means to be valid.

    """
    key = f'views.get_sock_names.{master_name}'
    users = cache.get(key)
    if users is None:
        case = CacheableSpiCase.get(wiki, master_name)
        # Need to work out cache invalidation
        usernames = [user_info.username for user_info in case.users]
        invalid_names = wiki.validate_usernames(usernames)
        known_socks = _users_from_category(wiki, f'Wikipedia sockpuppets of {master_name}')
        suspected_socks = _users_from_category(wiki, f'Suspected Wikipedia sockpuppets of {master_name}')
        users = []
        for user_info in case.users:
            name = user_info.username
            valid = name not in invalid_names
            sock_type = _classify_sock_type(name, known_socks, suspected_socks)
            user = ValidatedUser(name, user_info.date, valid, sock_type)
            if not valid:
                logger.warning('invalid username (%s) in case "%s"', user, master_name)
            users.append(user)
        cache.set(key, users, 300)
    return users


def _users_from_category(wiki, category_name):
    name_list = []
    pattern = re.compile(r'User:(.*)$')
    for member in wiki.category(category_name).members():
        m = pattern.match(member)
        if m:
            name_list.append(m[1])
    return name_list


def _classify_sock_type(name, known_socks, suspected_socks):
    if name in known_socks:
        return SockType.KNOWN
    if name in suspected_socks:
        return SockType.SUSPECTED
    return SockType.NONE
