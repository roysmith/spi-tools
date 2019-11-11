from collections import namedtuple, defaultdict
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from mwclient import Site
import mwparserfromhell

from .forms import CaseNameForm, IpRangeForm
from .spi_utils import SpiCase, SpiIpInfo, SpiSourceDocument


SITE_NAME = 'en.wikipedia.org'

IpSummary = namedtuple('IpSummary', 'ip, spi_dates')


class IndexView(View):
    def get(self, request):
        form = CaseNameForm()
        context = {'form': form} 
        return render(request, 'spi/index.dtl', context)

    def post(self, request):
        form = CaseNameForm(request.POST)
        if form.is_valid():
            case_name = form.cleaned_data['case_name']
            return redirect('spi-ip-analysis', case_name)
        return render(request, 'spi/index.dtl', context)


class IpAnalysisView(View):
    def get(self, request, case_name):
        ip_data = defaultdict(list)
        for i in get_spi_case_ips(case_name):
            ip_data[i.ip].append(i.date)
        summaries = [IpSummary(ip, sorted(ip_data[ip])) for ip in ip_data]
        summaries.sort()
        context = {'case_name': case_name,
                   'ip_summaries': summaries,
        }
        return render(request, 'spi/ip-analysis.dtl', context)


def get_spi_case_ips(master_name):
    "Returns a iterable over SpiIpInfos"
    site = Site(SITE_NAME)
    case_page = 'Wikipedia:Sockpuppet investigations/%s' % master_name
    archive_page = '%s/Archive' % case_page
    case = SpiCase(SpiSourceDocument(site.pages[case_page].text(), case_page),
                   SpiSourceDocument(site.pages[archive_page].text(), archive_page))
    return case.find_all_ips()
