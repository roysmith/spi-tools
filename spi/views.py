from collections import defaultdict
from dataclasses import dataclass
from typing import List
import logging
import urllib.request
import urllib.parse
import datetime
import itertools
import functools
import heapq

import requests

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


from wiki_interface import Wiki
from wiki_interface.block_utils import UserBlockHistory
from .forms import CaseNameForm, SockSelectForm, UserInfoForm
from .spi_utils import SpiIpInfo, SpiCase


logger = logging.getLogger('spi.views')


EDITOR_INTERACT_BASE = "https://tools.wmflabs.org/sigma/editorinteract.py"
TIMECARD_BASE = 'https://xtools.wmflabs.org/api/user/timecard/en.wikipedia.org'


@dataclass(frozen=True, order=True)
class IpSummary:
    ip_address: str
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
        context = {'form': form}
        if form.is_valid():
            case_name = form.cleaned_data['case_name']
            use_archive = form.cleaned_data['use_archive']
            if 'ip-info-button' in request.POST:
                return redirect('spi-ip-analysis', case_name)
            if 'sock-info-button' in request.POST:
                return redirect('%s?archive=%d' % (reverse('spi-sock-info', args=[case_name]),
                                                   use_archive))
            if 'sock-select-button' in request.POST:
                return redirect('%s?archive=%d' % (reverse('spi-sock-select', args=[case_name]),
                                                   use_archive))
            if 'g5-button' in request.POST:
                return redirect('%s?archive=%d' % (reverse('spi-g5', args=[case_name]),
                                                   use_archive))
            message = 'No known button in POST (%s)' % request.POST.keys()
            logger.error(message)
            context['error'] = message

        return render(request, 'spi/index.dtl', context)


class IpAnalysisView(View):
    def get(self, request, case_name):
        wiki = Wiki()
        ip_data = defaultdict(list)
        for i in SpiCase.get_case(wiki, case_name).find_all_ips():
            ip_data[i.ip_address].append(i.date)
        summaries = [IpSummary(ip, sorted(ip_data[ip])) for ip in ip_data]
        summaries.sort()
        context = {'case_name': case_name,
                   'ip_summaries': summaries}
        return render(request, 'spi/ip-analysis.dtl', context)


def get_sock_names(wiki, master_name, use_archive=True):
    """Returns a iterable over SpiUserInfos.

    If use_archive is true, both the current case and any existing
    archive is used.  Otherwise, just the current case.

    """
    case = SpiCase.get_case(wiki, master_name, use_archive)
    return case.find_all_users()


class SockInfoView(View):
    def get(self, request, case_name):
        wiki = Wiki()
        socks = []
        use_archive = int(request.GET.get('archive', 1))
        for sock in get_sock_names(wiki, case_name, use_archive):
            socks.append(sock)
        summaries = list({self.make_user_summary(wiki, sock) for sock in socks})
        # This is a hack to make users with no registration time sort to the
        # beginning of the list.  We need to do something smarter here.
        summaries.sort(key=lambda x: x.registration_time or "")
        context = {'case_name': case_name,
                   'summaries': summaries}
        return render(request, 'spi/sock-info.dtl', context)


    @staticmethod
    def make_user_summary(wiki, sock):
        username = sock.username
        return UserSummary(username, wiki.get_registration_time(username))


class SockSelectView(View):
    def get(self, request, case_name):
        wiki = Wiki()
        use_archive = int(request.GET.get('archive', 1))
        user_infos = list(get_sock_names(wiki, case_name, use_archive))
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
        selected_socks = [urllib.parse.unquote(f.replace('sock_', '', 1))
                          for f in request.POST if f.startswith('sock_')]
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
            data = form.cleaned_data
            url = (f'{reverse("spi-user-activities", args=[user_name])}'
                   f'?count={data["count"]}'
                   f'&main={int(data["main"])}'
                   f'&draft={int(data["draft"])}'
                   f'&other={int(data["other"])}')
            logger.debug("Redirecting to: %s", url)
            return redirect(url)
        logger.debug("post: not valid")
        context = {'user_name': user_name,
                   'form': form}
        return render(request, 'spi/user-info.dtl', context)


class UserActivitiesView(LoginRequiredMixin, View):
    def get(self, request, user_name):
        wiki = Wiki(request)
        user_name = urllib.parse.unquote_plus(user_name)
        logger.debug("user_name = %s", user_name)
        count = int(request.GET.get('count', '1'))
        namespace_filter = functools.partial(self.check_namespaces,
                                             wiki.namespace_values,
                                             bool(int(request.GET.get('main', 0))),
                                             bool(int(request.GET.get('draft', 0))),
                                             bool(int(request.GET.get('other', 0))))
        active = wiki.user_contributions(user_name)

        deleted = wiki.deleted_user_contributions(user_name)
        merged = heapq.merge(active, deleted, reverse=True)
        filtered = itertools.filterfalse(namespace_filter, merged)
        counted = list(itertools.islice(filtered, count))
        daily_activities = self.group_by_day(counted)
        context = {'user_name': user_name,
                   'daily_activities': daily_activities}
        return render(request, 'spi/user-activities.dtl', context)


    # https://github.com/roysmith/spi-tools/issues/51
    @staticmethod
    def check_namespaces(namespace_values, main, draft, other, contrib):
        if contrib.namespace == namespace_values['']:
            return not main
        if contrib.namespace == namespace_values['Draft']:
            return not draft
        return not other


    @staticmethod
    def group_by_day(activities):
        """Group activities into daily chunks.  Assumes that activities is
        sorted in chronological order.

        """
        previous_date = None

        # https://getbootstrap.com/docs/4.0/content/tables/#contextual-classes
        date_groups = ['primary', 'secondary']

        daily_activities = []
        for activity in activities:
            this_date = activity.timestamp.date()
            daily_activities.append((date_groups[0],
                                     activity.timestamp,
                                     'edit' if activity.is_live else 'deleted',
                                     activity.title,
                                     activity.comment))
            if this_date != previous_date:
                date_groups.reverse()
                previous_date = this_date
        return daily_activities


class TimecardView(View):
    def get(self, request, case_name):
        user_names = request.GET.getlist('users')
        data = {}
        for name in user_names:
            response = requests.get('%s/%s' % (TIMECARD_BASE, name))
            if response.status_code == requests.codes.ok: # pylint: disable=no-member
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
        wiki = Wiki()
        use_archive = int(request.GET.get('archive', 1))
        sock_names = [s.username for s in get_sock_names(wiki, case_name, use_archive)]

        history = UserBlockHistory(wiki.get_user_blocks(case_name))

        page_creations = []
        for contrib in wiki.user_contributions(sock_names, show="new"):
            if history.is_blocked_at(contrib.timestamp):
                title = contrib.title
                page = wiki.page(title)
                if page.exists():
                    page_creations.append(G5Summary(title,
                                                    contrib.user_name,
                                                    contrib.timestamp,
                                                    self.g5_score(page)))

        context = {'case_name': case_name,
                   'page_creations': page_creations,
                   }
        return render(request, 'spi/g5.dtl', context)


    @staticmethod
    def g5_score(page):
        revisions = list(itertools.islice(page.revisions(), 50))
        if len(revisions) >= 50:
            return G5Score("unlikely", "50 or more revisions")
        editors = {r.user_name for r in revisions}
        if len(editors) == 1:
            return G5Score("likely", "only one editor")
        return G5Score("unknown")
