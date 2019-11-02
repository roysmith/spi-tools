from collections import namedtuple
from django.shortcuts import render
from mwclient import Site
import mwparserfromhell

from .forms import SummaryForm
from .spi_utils import SpiCase


SITE_NAME = 'en.wikipedia.org'


def index(request):
    context = {}
    return render(request, 'spi/index.dtl', context)


def summary(request):
    if request.method == 'POST':
        form = SummaryForm(request.POST)
        if form.is_valid():
            master_name = form.cleaned_data['master_name']
            context = {'form': form,
                       'master_name': master_name,
                       'ip_infos': sorted(get_spi_case_ips(master_name)),
            }
            return render(request, 'spi/summary.dtl', context)
    else:
        form = SummaryForm()
    context = {'form': form} 
    return render(request, 'spi/summary.dtl', context)


def get_spi_case_ips(master_name):
    "Returns a list of SpiIpInfos"
    site = Site(SITE_NAME)
    case_page = 'Wikipedia:Sockpuppet investigations/%s' % master_name
    archive_page = '%s/Archive' % case_page
    case = SpiCase(site.pages[case_page].text(), site.pages[archive_page].text())
    return case.find_all_ips()
