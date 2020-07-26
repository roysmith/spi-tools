from collections import defaultdict
from dataclasses import dataclass
from typing import List
import logging
import urllib.request
import urllib.parse
import time
import datetime
import itertools
import functools
import heapq

import requests

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
import django.contrib.auth
from django.contrib.auth.mixins import LoginRequiredMixin

from mwclient import Site
import mwclient.listing

from .forms import CaseNameForm, SockSelectForm, UserInfoForm
from .spi_utils import SpiCase, SpiIpInfo, SpiSourceDocument
from tools_app import settings
from .block_utils import BlockMap


logger = logging.getLogger('view')



EDITOR_INTERACT_BASE = "https://tools.wmflabs.org/sigma/editorinteract.py"
TIMECARD_BASE = 'https://xtools.wmflabs.org/api/user/timecard/en.wikipedia.org'


def datetime_from_struct(time_struct):
    return datetime.datetime.fromtimestamp(time.mktime(time_struct), tz=datetime.timezone.utc)


def get_site(request):
    """Return a mwclient.Site object.

    If the user is logged in, this will include OAUTH consumer and access
    credentials.  Otherwise, it will be an anonymous connection.

    """
    user = django.contrib.auth.get_user(request)

    # It's not clear if we need to bother checking to see if the user
    # is authenticated.  Maybe with an AnonymousUser, everything just
    # works?  If so, these two code paths could be merged.
    if user.is_anonymous:
        auth_info = {}
    else:
        access_token = (user
                        .social_auth
                        .get(provider='mediawiki')
                        .extra_data['access_token'])
        auth_info = {
            'consumer_token': settings.SOCIAL_AUTH_MEDIAWIKI_KEY,
            'consumer_secret': settings.SOCIAL_AUTH_MEDIAWIKI_SECRET,
            'access_token': access_token['oauth_token'],
            'access_secret': access_token['oauth_token_secret']
        }

    return Site(settings.MEDIAWIKI_SITE_NAME,
                clients_useragent=settings.MEDIAWIKI_USER_AGENT,
                **auth_info)


@dataclass(frozen=True)
class IpSummary:
    ip: str
    spi_dates: List[SpiIpInfo]


@dataclass(frozen=True)
class UserSummary:
    username: str
    registration_time: str

    def urlencoded_username(self):
        return urllib.parse.quote_plus(self.username)


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
            if 'g5-button' in request.POST:
                base_url = reverse('spi-g5', args=[case_name])
                url = base_url + '?archive=%d' % int(use_archive)
                return redirect(url)
            print("Egad, unknown button!")
        context = {'form': form}
        return render(request, 'spi/index.dtl', context)


class IpAnalysisView(View):
    def get(self, request, case_name):
        site = get_site(request)
        ip_data = defaultdict(list)
        for i in self.get_spi_case_ips(site, case_name):
            ip_data[i.ip].append(i.date)
        summaries = [IpSummary(ip, sorted(ip_data[ip])) for ip in ip_data]
        summaries.sort()
        context = {'case_name': case_name,
                   'ip_summaries': summaries}
        return render(request, 'spi/ip-analysis.dtl', context)


    def get_spi_case_ips(self, site, master_name):
        "Returns a iterable over SpiIpInfos"
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


def get_registration_time(site, user):
    '''Return the registration time for a user as a string.

    If the registration time can't be determined, returns None.

    '''
    registrations = site.users(users=[user], prop=['registration'])
    userinfo = registrations.next()
    try:
        return userinfo['registration']
    except KeyError:
        return None


def get_sock_names(site, master_name, use_archive=True):
    """Returns a iterable over SpiUserInfos.

    If use_archive is true, both the current case and any existing
    archive is used.  Otherwise, just the current case.

    """
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


def make_user_summary(site, sock):
    return UserSummary(sock.username,
                       get_registration_time(site, sock.username))


class SockInfoView(View):
    def get(self, request, case_name):
        site = get_site(request)
        socks = []
        use_archive = int(request.GET.get('archive', 1))
        for sock in get_sock_names(site, case_name, use_archive):
            socks.append(sock)
        summaries = list({make_user_summary(site, sock) for sock in socks})
        # This is a hack to make users with no registration time sort to the
        # beginning of the list.  We need to do something smarter here.
        summaries.sort(key=lambda x: x.registration_time or "")
        context = {'case_name': case_name,
                   'summaries': summaries}
        return render(request, 'spi/sock-info.dtl', context)


class SockSelectView(View):
    def get(self, request, case_name):
        site = get_site(request)
        use_archive = int(request.GET.get('archive', 1))
        user_infos = list(get_sock_names(site, case_name, use_archive))
        return render(request,
                      'spi/sock-select.dtl',
                      self.build_context(case_name, user_infos))

    def post(self, request, case_name):
        form = SockSelectForm(request.POST)
        if form.is_valid():
            logger.debug("post: valid")

            if 'interaction-analyzer-button' in request.POST:
                url = f'{EDITOR_INTERACT_BASE}?{self.get_encoded_users(request)}'
                return redirect(url)

            if 'timecard-button' in request.POST:
                url = '%s?%s' % (reverse("spi-timecard", args=[case_name]),
                                 self.get_encoded_users(request))
                return redirect(url)

            logger.error("Unknown button!")

        logger.debug("post: not valid")
        context = {'case_name': case_name,
                   'form': form}
        return render(request, 'spi/sock-select.dtl', context)


    @staticmethod
    def get_encoded_users(request):
        """Get all the socks which have been selected from the SockSelectForm.

        A string of the form "users=sock_1&users=sock_2....users=sock_n" is returned.

        """
        selected_fields = [urllib.parse.unquote(f.replace('sock_', '', 1))
                           for f in request.POST if f.startswith('sock_')]
        selected_socks = [f for f in selected_fields]
        query_items = [('users', sock) for sock in selected_socks]
        params = urllib.parse.urlencode(query_items)
        return params


    @staticmethod
    def build_context(case_name, user_infos):
        users_by_name = {user.username: user for user in user_infos}
        names = list({user.username for user in user_infos})
        dates = [users_by_name[name].date for name in names]
        form = SockSelectForm.build(names)
        return {'case_name': case_name,
                'form_info': zip(form, names, dates)}


class UserInfoView(View):
    def get(self, request, user_name):
        form = UserInfoForm(initial={'count': 100,
                                     'main': True,
                                     'draft': True,
                                     })
        context = {'user_name': urllib.parse.unquote_plus(user_name),
                   'form': form}
        return render(request, 'spi/user-info.dtl', context)

    def post(self, request, user_name):
        form = UserInfoForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            main = int(form.cleaned_data['main'])
            draft = int(form.cleaned_data['draft'])
            other = int(form.cleaned_data['other'])

            base_url = reverse('spi-user-activities', args=[user_name])
            url = f'{base_url}?count={count}&main={main}&draft={draft}&other={other}'
            logger.debug("Redirecting to: %s", url)
            return redirect(url)
        logger.debug("post: not valid")
        context = {'user_name': user_name,
                   'form': form}
        return render(request, 'spi/user-info.dtl', context)


class UserActivitiesView(LoginRequiredMixin, View):
    def get(self, request, user_name):
        site = get_site(request)
        user_name = urllib.parse.unquote_plus(user_name)
        logger.debug("user_name = %s", user_name)
        count = int(request.GET.get('count', '1'))
        namespace_filter = functools.partial(self.check_namespaces,
                                             bool(int(request.GET.get('main', 0))),
                                             bool(int(request.GET.get('draft', 0))),
                                             bool(int(request.GET.get('other', 0))))

        active = self.contribution_activities(site, user_name)
        deleted = self.deleted_contribution_activities(site, user_name)
        merged = heapq.merge(active, deleted, reverse=True)
        filtered = itertools.filterfalse(namespace_filter, merged)
        counted = itertools.islice(filtered, count)
        daily_activities = self.group_by_day(counted)

        context = {'user_name': user_name,
                   'daily_activities': daily_activities}
        return render(request, 'spi/user-activities.dtl', context)


    # https://github.com/roysmith/spi-tools/issues/50
    @staticmethod
    def check_namespaces(main, draft, other, activity):
        _, _, title, _ = activity
        if not ':' in title:
            return not main
        name_space, _ = title.split(':', 1)
        name_space = name_space.lower().strip()
        if name_space == 'draft':
            return not draft
        return not other


    def contribution_activities(self, site, user_name):
        for uc in site.usercontributions(user_name):
            logger.debug("uc = %s", uc)
            timestamp = datetime_from_struct(uc['timestamp'])
            title = uc['title']
            comment = uc['comment']
            yield timestamp, 'edit', title, comment


    def deleted_contribution_activities(self, site, user_name):
        kwargs = dict(mwclient.listing.List.generate_kwargs('adr', user=user_name))
        listing = mwclient.listing.List(site,
                                        'alldeletedrevisions',
                                        'adr',
                                        limit=20,
                                        uselang=None,
                                        **kwargs)

        for page in listing:
            title = page['title']
            for revision in page['revisions']:
                logger.debug("deleted revision = %s", revision)
                rev_ts = revision['timestamp']
                if rev_ts.endswith('Z'):
                    timestamp = datetime.datetime.fromisoformat(rev_ts[:-1] + '+00:00')
                else:
                    raise ValueError("Unparsable timestamp: %s" % rev_ts)
                title = page['title']
                comment = revision['comment']
                yield timestamp, 'deleted', title, comment


    def group_by_day(self, activities):
        """Group activities into daily chunks.  Assumes that activities is
        sorted in chronological order.

        """
        previous_date = None

        # https://getbootstrap.com/docs/4.0/content/tables/#contextual-classes
        date_groups = ['primary', 'secondary']

        daily_activities = []
        for timestamp, activity_type, title, comment in activities:
            this_date = timestamp.date()
            if this_date != previous_date:
                date_groups.reverse()
                previous_date = this_date
            daily_activities.append((date_groups[0], timestamp, activity_type, title, comment))
        return daily_activities


class TimecardView(View):
    def get(self, request, case_name):
        user_names = request.GET.getlist('users')
        data = {}
        for name in user_names:
            response = requests.get('%s/%s' % (TIMECARD_BASE, name))
            if response.status_code == requests.codes.ok:
                timecard = response.json()['timecard']
                data[name] = [{'x': t['hour'], 'y': t['day_of_week'], 'r': t['scale']}
                              for t in timecard
                              if 'scale' in t]
            else:
                data[name] = []

        context = {'case_name': case_name,
                   'users': user_names,
                   'data': data}
        return render(request, 'spi/timecard.dtl', context)


@dataclass(frozen=True)
class G5Summary:
    title: str
    user: str
    timestamp: datetime.datetime
    score: str


@dataclass(frozen=True)
class G5Score:
    rating: str
    reason: str = ''


class G5View(View):
    def get(self, request, case_name):
        site = get_site(request)
        use_archive = int(request.GET.get('archive', 1))
        socks = get_sock_names(site, case_name, use_archive)
        sock_names = [s.username for s in socks]
        for sock_name in sock_names:
            if '|' in sock_name:
                raise RuntimeError(f'"{sock_name}" has a "|" in it')

        block_map = BlockMap(site.blocks(users=case_name))

        page_creations = []
        for contrib in site.usercontributions('|'.join(sock_names), show="new"):
            timestamp = datetime_from_struct(contrib['timestamp'])
            if block_map.is_blocked_at(timestamp):
                summary = self.build_summary(site,
                                             contrib['title'],
                                             contrib['user'],
                                             timestamp)
                if summary:
                    page_creations.append(summary)

        context = {'case_name': case_name,
                   'block_map': block_map,
                   'page_creations': page_creations,
                   }
        return render(request, 'spi/g5.dtl', context)


    def build_summary(self, site, title, user, timestamp):
        page = site.pages[title]
        if page.exists:
            return G5Summary(title, user, timestamp, self.g5_score(page))
        return None


    def g5_score(self, page):
        revisions = list(itertools.islice(page.revisions(), 50))
        if len(revisions) >= 50:
            return G5Score("unlikely", "50 or more revisions")
        editors = {r['user'] for r in revisions}
        if len(editors) == 1:
            return G5Score("likely", "only one editor")
        return G5Score("unknown")
