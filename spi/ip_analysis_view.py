from collections import defaultdict
from dataclasses import dataclass
import logging
from typing import List

from django.shortcuts import render

from spi.spi_utils import CacheableSpiCase, SpiIpInfo
from spi.spi_view import SpiView


logger = logging.getLogger('spi.views.ip_analysis_view')


@dataclass(frozen=True, order=True)
class IpSummary:
    ip_address: str
    spi_dates: List[SpiIpInfo]


class IpAnalysisView(SpiView):
    def get(self, request, case_name):
        ip_data = defaultdict(list)
        for i in CacheableSpiCase.get(self.wiki, case_name).ip_addresses:
            ip_data[i.ip_address].append(i.date)
        summaries = [IpSummary(ip, sorted(ip_data[ip])) for ip in ip_data]
        summaries.sort()
        context = {'case_name': case_name,
                   'ip_summaries': summaries}
        return render(request, 'spi/ip-analysis.html', context)
