from collections import namedtuple
from django.shortcuts import render
from mwclient import Site
import mwparserfromhell

from .forms import SummaryForm
from .spi_utils import SPICase


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
                       'ips': get_spi_case_ips(master_name),
            }
            return render(request, 'spi/summary.dtl', context)
    else:
        form = SummaryForm()
    context = {'form': form} 
    return render(request, 'spi/summary.dtl', context)


def get_spi_case_ips(master_name):
    "Returns a list of IP addresses as strings"
    site = Site(SITE_NAME)
    case_page = 'Wikipedia:Sockpuppet investigations/%s' % master_name
    archive_page = '%s/Archive' % case_page
    case = SPICase(site.pages[case_page].text(), site.pages[archive_page].text())
    spi_case_ips = case.find_all_ips()
    ips = sorted(s.ip for s in spi_case_ips)
    return ips

