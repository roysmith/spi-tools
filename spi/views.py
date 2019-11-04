from collections import namedtuple
from django.shortcuts import render, redirect
from django.urls import reverse
from mwclient import Site
import mwparserfromhell

from .forms import CaseNameForm
from .spi_utils import SpiCase, SpiIpInfo


SITE_NAME = 'en.wikipedia.org'


def index(request):
    if request.method == 'POST':
        form = CaseNameForm(request.POST)
        if form.is_valid():
            case_name = form.cleaned_data['case_name']
            return redirect('spi-ip-analysis', case_name)
    else:
        form = CaseNameForm()
    context = {'form': form} 
    return render(request, 'spi/index.dtl', context)


def ip_analysis(request, case_name):
    infos = sorted(get_spi_case_ips(case_name))
    network = SpiIpInfo.find_common_network(infos)
    context = {'case_name': case_name,
               'network': network,
               'ip_infos': infos,
    }
    return render(request, 'spi/ip-analysis.dtl', context)


def get_spi_case_ips(master_name):
    "Returns a list of SpiIpInfos"
    site = Site(SITE_NAME)
    case_page = 'Wikipedia:Sockpuppet investigations/%s' % master_name
    archive_page = '%s/Archive' % case_page
    case = SpiCase(site.pages[case_page].text(), site.pages[archive_page].text())
    return case.find_all_ips()
