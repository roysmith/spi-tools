from collections import namedtuple, defaultdict
from pprint import pprint
import logging
import urllib.request
import urllib.parse
import time
import datetime
import itertools

import requests

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.forms import BooleanField
import django.contrib.auth
from django.contrib.auth.mixins import LoginRequiredMixin

from mwclient import Site
import mwclient.listing
import mwparserfromhell

from .forms import CaseNameForm, IpRangeForm, SockSelectForm
from .spi_utils import SpiCase, SpiIpInfo, SpiSourceDocument
from tools_app import settings

logger = logging.getLogger('view')


SITE_NAME = 'en.wikipedia.org'
EDITOR_INTERACT_BASE = "https://tools.wmflabs.org/sigma/editorinteract.py"
TIMECARD_BASE = 'https://xtools.wmflabs.org/api/user/timecard/en.wikipedia.org'

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
            if 'sock-select-button' in request.POST:
                base_url = reverse('spi-sock-select', args=[case_name])
                url = base_url + '?archive=%d' % int(use_archive)
                return redirect(url)
            print("Egad, unknown button!")
        context = {'form': form}
        return render(request, 'spi/index.dtl', context)


class IpAnalysisView(View):
    def get(self, request, case_name):
        ip_data = defaultdict(list)
        for i in self.get_spi_case_ips(case_name):
            ip_data[i.ip].append(i.date)
        summaries = [IpSummary(ip, sorted(ip_data[ip])) for ip in ip_data]
        summaries.sort()
        context = {'case_name': case_name,
                   'ip_summaries': summaries,
        }
        return render(request, 'spi/ip-analysis.dtl', context)


    def get_spi_case_ips(self, master_name):
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


def make_user_summary(sock):
    return UserSummary(sock.username,
                       get_registration_time(sock.username))


class SockInfoView(View):
    def get(self, request, case_name):
        socks = []
        use_archive = int(request.GET.get('archive', 1))
        for sock in get_sock_names(case_name, use_archive):
            socks.append(sock)
        summaries = list({make_user_summary(sock) for sock in socks})
        # This is a hack to make users with no registration time sort to the
        # beginning of the list.  We need to do something smarter here.
        summaries.sort(key=lambda x: x.registration_time or "")
        context = {'case_name': case_name,
                   'summaries': summaries,
        }
        return render(request, 'spi/sock-info.dtl', context)


class SockSelectView(View):
    def get(self, request, case_name):
        use_archive = int(request.GET.get('archive', 1))
        user_infos = list(get_sock_names(case_name, use_archive))
        return render(request,
                      'spi/sock-select.dtl',
                      self.build_context(case_name, user_infos))

    def post(self, request, case_name):
        form = SockSelectForm(request.POST)
        if form.is_valid():
            logger.debug("post: valid")
            if 'interaction-analyzer-button' in request.POST:
                selected_fields = [urllib.parse.unquote(f.replace('sock_', '', 1))
                                   for f in request.POST if f.startswith('sock_')]
                selected_socks = [f for f in selected_fields]
                query_items = [('users', sock) for sock in selected_socks]
                params = urllib.parse.urlencode(query_items)
                url = "%s?%s" % (EDITOR_INTERACT_BASE, params)
                logger.debug("Redirecting to: %s" % url)
                return redirect(url)
            if 'timecard-button' in request.POST:
                selected_fields = [urllib.parse.unquote(f.replace('sock_', '', 1))
                                   for f in request.POST if f.startswith('sock_')]
                selected_socks = [f for f in selected_fields]
                query_items = [('users', sock) for sock in selected_socks]
                params = urllib.parse.urlencode(query_items)
                url = "%s?%s" % (reverse('spi-timecard', args=[case_name]), params)
                logger.debug("Redirecting to: %s" % url)
                return redirect(url)
            print("Egad, unknown button!")
        logger.debug("post: not valid")
        context = {'case_name': case_name,
                   'form': form}
        return render(request, 'spi/sock-select.dtl', context)

    @staticmethod
    def build_context(case_name, user_infos):
        users_by_name = {user.username: user for user in user_infos}
        names = list({user.username for user in user_infos})
        dates = [users_by_name[name].date for name in names]
        form = SockSelectForm.build(names)
        return {'case_name': case_name,
                'form_info': zip(form, names, dates),
        }


class UserInfoView(View):
    def get(self, request, user_name):
        context = {'user_name': user_name}
        return render(request, 'spi/user-info.dtl', context)


class UserActivitiesView(LoginRequiredMixin, View):
    def get(self, request, user_name):
        access_token = (django.contrib.auth.get_user(request)
                        .social_auth
                        .get(provider='mediawiki')
                        .extra_data['access_token'])
        site = Site(SITE_NAME,
                    consumer_token=settings.SOCIAL_AUTH_MEDIAWIKI_KEY,
                    consumer_secret=settings.SOCIAL_AUTH_MEDIAWIKI_SECRET,
                    access_token=access_token['oauth_token'],
                    access_secret=access_token['oauth_token_secret'],
                    clients_useragent=f'{settings.TOOL_NAME} (toolforge)')

        activities = []

        logger.debug("user_name = %s" % user_name)
        for uc in itertools.islice(site.usercontributions(user_name), 10):
            logger.debug("uc = %s" % uc)
            timestamp = datetime.datetime.fromtimestamp(time.mktime(uc['timestamp']), tz=datetime.timezone.utc)
            title = uc['title']
            comment = uc['comment']
            activities.append((timestamp, 'edit', title, comment))

        kwargs = dict(mwclient.listing.List.generate_kwargs('adr',
                                                            user=user_name))
        logger.debug("kwargs = %s" % kwargs)
        listing = mwclient.listing.List(site,
                                        'alldeletedrevisions',
                                        'adr',
                                        limit=20,
                                        uselang=None,
                                        **kwargs)

        for page in itertools.islice(listing, 10):
            title = page['title']
            for revision in page['revisions']:
                logger.debug("deleted = %s" % revision)
                ts = revision['timestamp']
                if ts.endswith('Z'):
                    timestamp = datetime.datetime.fromisoformat(ts[:-1] + '+00:00')
                else:
                    raise ValueError("Unparsable timestamp: %s" % ts)
                title = page['title']
                comment = revision['comment']
                activities.append((timestamp, 'deleted', title, comment))

        activities.sort(reverse=True)
        previous_date = None
        date_groups = ['primary', 'secondary']   # https://getbootstrap.com/docs/4.0/content/tables/#contextual-classes
        daily_activities = []
        for a in activities:
            timestamp, activity_type, title, comment = a
            this_date = timestamp.date()
            if this_date != previous_date:
                date_groups.reverse()
                previous_date = this_date
            daily_activities.append((date_groups[0], timestamp, activity_type, title, comment))


        context = {'user_name': user_name,
                   'daily_activities': daily_activities,
        }
        return render(request, 'spi/user-activities.dtl', context)


class TimecardView(View):
    def get(self, request, case_name):
        user_names = request.GET.getlist('users')
        data = {}
        for name in user_names:
            r = requests.get('%s/%s' % (TIMECARD_BASE, name))
            if r.status_code == requests.codes.ok:
                timecard = r.json()['timecard']
                data[name] = [{'x': t['hour'], 'y': t['day_of_week'], 'r': t['scale']}
                              for t in timecard
                              if 'scale' in t]
            else:
                data[name] = []

        context = {'case_name': case_name,
                   'users': user_names,
                   'data': data,
        }
        return render(request, 'spi/timecard.dtl', context)
