from datetime import timedelta
import logging
import json

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin

from spi.views import get_sock_names, SockType
from wiki_interface import Wiki

logger = logging.getLogger('spi.views.cu_log_view')


# Only usres listed here will be allowed to access these views.
# This is a temporary hack.
AUTHORIZED_USERS = ['RoySmith', 'Yamla', 'Girth Summit']


class CuLogView(UserPassesTestMixin, View):
    def test_func(self):
        return self.is_authorized(self.request)


    @staticmethod
    def is_authorized(request):
        return request.user.username in AUTHORIZED_USERS


    def get(self, request, case_name):
        logger.info(request)
        wiki = Wiki(request)
        user_infos = list(get_sock_names(wiki, case_name))
        sock_names = [ui.username for ui in user_infos if ui.valid and ui.sock_type >= SockType.SUSPECTED]

        get_ip_entries = []
        for name in sock_names:
            get_ip_entries.extend(wiki.get_cu_log(target=name))

        get_user_entries = []
        ips = set()
        for entry in get_ip_entries:
            if entry.type == 'userips':
                to_ts = entry.timestamp
                from_ts = to_ts + timedelta(minutes=15)
                candidate_entries = wiki.get_cu_log(user=entry.checkuser,
                                                    from_ts=from_ts,
                                                    to_ts=to_ts)
                for ce in candidate_entries:
                    if ce.type == 'ipedits' and entry.target in ce.reason:
                        ips.add(ce.target)
                        get_user_entries.append(ce)

        all_entries = get_ip_entries + get_user_entries
        all_entries.sort(key=lambda e: e.timestamp)

        context = {'case_name': case_name,
                   'log_entries': all_entries,
                   'ips': sorted(ips),
        }
        return render(request, 'spi/cu_log.html', context)
