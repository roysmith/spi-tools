from collections import namedtuple, defaultdict
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from mwclient import Site
import mwparserfromhell
from pprint import pprint

from .forms import CaseNameForm, IpRangeForm
from .spi_utils import SpiCase, SpiIpInfo, SpiSourceDocument


SITE_NAME = 'en.wikipedia.org'

IpSummary = namedtuple('IpSummary', 'ip, spi_dates')
UserSummary = namedtuple('UserSummary', 'username, registration_time')


class IndexView(View):
    def get(self, request):
        form = CaseNameForm()
        context = {'form': form} 
        return render(request, 'spi/index.dtl', context)

    def post(self, request):
        form = CaseNameForm(request.POST)
        if form.is_valid():
            case_name = form.cleaned_data['case_name']
            use_archive = form.cleaned_data['use_archive']
            if 'ip-info-button' in request.POST:
                return redirect('spi-ip-analysis', case_name)
            if 'sock-info-button' in request.POST:
                base_url = reverse('spi-sock-info', args=[case_name])
                url = base_url + '?archive=%d' % int(use_archive)
                return redirect(url)
            print("Egad, unknown button!")
        context = {'form': form}
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

class SockInfoView(View):
    def get(self, request, case_name):
        socks = []
        use_archive = int(request.GET.get('archive', 1))
        for sock in get_sock_names(case_name, use_archive):
            socks.append(sock)
        summaries = [make_user_summary(sock) for sock in socks]
        # This is a hack to make users with no registration time sort to the
        # beginning of the list.  We need to do something smarter here.
        summaries.sort(key=lambda x: x.registration_time or "")
        context = {'case_name': case_name,
                   'summaries': summaries,
        }
        return render(request, 'spi/sock-info.dtl', context)


class UserInfoView(View):
    def get(self, request, user_name):
        context = {'user_name': user_name}
        return render(request, 'spi/user-info.dtl', context)


def make_user_summary(sock):
    return UserSummary(sock.username,
                       get_registration_time(sock.username))


def get_registration_time(user):
    '''Return the registration time for a user as a string.

    If the registration time can't be determined, returns None.

    '''
    site = Site(SITE_NAME)
    r = site.users(users=[user], prop=['registration'])
    userinfo = r.next()
    try:
        return userinfo['registration']
    except KeyError:
        return None


def get_spi_case_ips(master_name):
    "Returns a iterable over SpiIpInfos"
    site = Site(SITE_NAME)
    case_title = 'Wikipedia:Sockpuppet investigations/%s' % master_name
    archive_title = '%s/Archive' % case_title

    case_doc = SpiSourceDocument(site.pages[case_title].text(), case_title)
    docs = [case_doc]

    archive_text = site.pages[archive_title].text()
    if archive_text:
        archive_doc = SpiSourceDocument(archive_text, archive_title)
        docs.append(archive_doc)

    case = SpiCase(*docs)
    return case.find_all_ips()


def get_sock_names(master_name, use_archive=True):
    """Returns a iterable over SpiUserInfos.

    If use_archive is true, both the current case and any existing
    archive is used.  Otherwise, just the current case.

    """
    site = Site(SITE_NAME)
    case_title = 'Wikipedia:Sockpuppet investigations/%s' % master_name
    archive_title = '%s/Archive' % case_title

    case_doc = SpiSourceDocument(site.pages[case_title].text(), case_title)
    docs = [case_doc]

    archive_text = use_archive and site.pages[archive_title].text()
    if archive_text:
        archive_doc = SpiSourceDocument(archive_text, archive_title)
        docs.append(archive_doc)

    case = SpiCase(*docs)
    return case.find_all_users()
