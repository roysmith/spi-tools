from datetime import timedelta
import logging
import json

from django.shortcuts import render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.conf import settings

from spi.spi_view import get_sock_names, SockType, SpiView


logger = logging.getLogger('spi.views.cu_log_view')


class CuLogView(UserPassesTestMixin, SpiView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)


    def test_func(self):
        return self.is_authorized(self.request, self.wiki)


    @staticmethod
    def is_authorized(request, wiki):
        return 'checkuser' in wiki.site.groups


    def get(self, request, case_name):
        logger.info(request)
        user_infos = list(get_sock_names(self.wiki, case_name))
        sock_names = [ui.username for ui in user_infos if ui.valid and ui.sock_type >= SockType.SUSPECTED]

        get_ip_entries = []
        for name in sock_names:
            get_ip_entries.extend(self.wiki.get_cu_log(target=name))

        get_user_entries = []
        ips = set()
        for entry in get_ip_entries:
            if entry.type == 'userips':
                to_ts = entry.timestamp
                from_ts = to_ts + timedelta(minutes=15)
                candidate_entries = self.wiki.get_cu_log(user=entry.checkuser,
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
