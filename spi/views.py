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
from django.core.cache import cache


from wiki_interface import Wiki
from wiki_interface.block_utils import BlockEvent, UnblockEvent, UserBlockHistory
from spi.forms import CaseNameForm, SockSelectForm, UserInfoForm
from spi.spi_utils import SpiIpInfo, SpiCase, get_current_case_names


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
        case_name = request.GET.get('caseName')
        context = {'form': form,
                   'choices': self.generate_select2_data(case_name=case_name),
                   }
        return render(request, 'spi/index.jinja', context)

    def post(self, request):
        form = CaseNameForm(request.POST)
        context = {'form': form,
                   'choices': self.generate_select2_data()
                   }
        if form.is_valid():
            case_name = form.cleaned_data['case_name']
            if 'ip-info-button' in request.POST:
                return redirect('spi-ip-analysis', case_name)
            if 'sock-select-button' in request.POST:
                return redirect('%s' % (reverse('spi-sock-select', args=[case_name])))
            if 'g5-button' in request.POST:
                return redirect('%s' % (reverse('spi-g5', args=[case_name])))
            message = 'No known button in POST (%s)' % request.POST.keys()
            logger.error(message)
            context['error'] = message

        return render(request, 'spi/index.jinja', context)

    @staticmethod
    def generate_select2_data(case_name=None):
        """Return data appropriate for the 'data' element of a select2.js
        configuration object.

        If case_name is provided, that option has the "selected"
        attribute set.  If it doesn't exist in the default list, it is
        added (and selected).

        """
        names = cache.get_or_set('IndexView.case_names', IndexView.get_case_names, 300)
        if case_name and case_name not in names:
            names.append(case_name)
        names.sort()

        # Leading empty element for select2.js placeholder.
        data = [{'id': '',
                 'text': ''}]
        for name in names:
            item = {'id': name,
                    'text': name}
            if name == case_name:
                item['selected'] = True
            data.append(item)

        return data


    @staticmethod
    def get_case_names():
        """Get the case names from the on-wiki SPI case listing.

        Returns a list of strings.

        """
        wiki = Wiki()
        return get_current_case_names(wiki)


class IpAnalysisView(View):
    def get(self, request, case_name):
        wiki = Wiki()
        ip_data = defaultdict(list)
        for i in SpiCase.for_master(wiki, case_name).find_all_ips():
            ip_data[i.ip_address].append(i.date)
        summaries = [IpSummary(ip, sorted(ip_data[ip])) for ip in ip_data]
        summaries.sort()
        context = {'case_name': case_name,
                   'ip_summaries': summaries}
        return render(request, 'spi/ip-analysis.jinja', context)


@dataclass(frozen=True, order=True)
class ValidatedUser:
    username: str
    date: str
    valid: bool


def get_sock_names(wiki, master_name):
    """Returns a iterable over ValidatedUsers

    Discovered usernames are checked for validity.  See
    Wiki.is_valid_username() for what it means to be valid.

    """
    key = f'views.get_sock_names.{master_name}'
    users = cache.get(key)
    if users is None:
        case = SpiCase.for_master(wiki, master_name)
        # Need to work out cache invalidation
        users = []
        for user_info in case.find_all_users():
            name = user_info.username
            valid = wiki.is_valid_username(name)
            user = ValidatedUser(name, user_info.date, valid)
            if not valid:
                logger.warning('invalid username (%s) in case "%s"', user, master_name)
            users.append(user)
        cache.set(key, users, 300)
    return users

class SockSelectView(View):
    def get(self, request, case_name):
        wiki = Wiki()
        user_infos = list(get_sock_names(wiki, case_name))
        return render(request,
                      'spi/sock-select.jinja',
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

            if 'timeline-button' in request.POST:
                url = '%s?%s' % (reverse("spi-timeline", args=[case_name]),
                                 self.get_encoded_users(request))
                return redirect(url)

            logger.error("Unknown button!")

        logger.debug("post: not valid")
        context = {'case_name': case_name,
                   'form': form}
        return render(request, 'spi/sock-select.jinja', context)


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
        logger.debug(user_infos)
        users_by_name = {user.username: user for user in user_infos}
        names = list({user.username for user in user_infos if user.valid})
        invalid_users = [user for user in user_infos if not user.valid]
        dates = [users_by_name[name].date for name in names]
        form = SockSelectForm.build(names)

        all_date_strings = set(user.date for user in user_infos if user.date)
        keyed_dates = [(datetime.datetime.strptime(d, '%d %B %Y'), d) for d in all_date_strings]

        return {'case_name': case_name,
                'form_info': zip(form, names, dates),
                'invalid_users': invalid_users,
                'dates': [v for (k, v) in sorted(keyed_dates)],
                }


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
        return render(request, 'spi/timecard.jinja', context)


@dataclass(frozen=True, order=True)
class TimelineEvent:
    """Most of the fields are self-explanatory.

    Description is a human-friendly (but short) phrase, details
    provides additional (optional) information.  For a log entry,
    these might be the type and action fields from the log event.

    Extra is optional additional information specific to the type of
    event.  Edit events, for example, use this for the tags.

    """
    timestamp: datetime
    user_name: str
    description: str
    details: str
    title: str
    comment: str
    extra: str = ''


class TimelineView(LoginRequiredMixin, View):
    def get(self, request, case_name):
        wiki = Wiki(request)
        user_names = request.GET.getlist('users')
        logger.debug("user_names = %s", user_names)

        self.tag_data = {}
        per_user_streams = [self.get_event_stream_for_user(wiki, user) for user in user_names]
        events = list(heapq.merge(*per_user_streams, reverse=True))
        # At this point, i.e. after the merge() output is consumed,
        # self.tag_data will be valid.
        tags = set()
        for tag_counts in self.tag_data.values():
            for tag in tag_counts:
                tags.add(tag)
        tag_list = sorted(tags)

        tag_table = []
        for user in user_names:
            counts = [(tag, self.tag_data[user][tag]) for tag in tag_list]
            tag_table.append((user, counts))

        context = {'case_name': case_name,
                   'user_names': user_names,
                   'events': events,
                   'tag_list': tag_list,
                   'tag_table': tag_table,
                   }
        return render(request, 'spi/timeline.jinja', context)


    def get_event_stream_for_user(self, wiki, user):
        """Returns an iterable over TimelineEvents.

        """
        user_streams = [self.get_contribs_for_user(wiki, user),
                        self.get_blocks_for_user(wiki, user),
                        self.get_log_events_for_user(wiki, user)]
        return heapq.merge(*user_streams, reverse=True)


    def get_contribs_for_user(self, wiki, user_name):
        """Returns an interable over TimelineEvents.

        As a side effect, updates self.tag_data.

        """
        self.tag_data[user_name] = defaultdict(int)
        active = wiki.user_contributions(user_name)
        deleted = wiki.deleted_user_contributions(user_name)
        for contrib in heapq.merge(active, deleted, reverse=True):
            for tag in contrib.tags:
                self.tag_data[user_name][tag] += 1

            yield TimelineEvent(contrib.timestamp,
                                contrib.user_name,
                                'edit',
                                '' if contrib.is_live else 'deleted',
                                contrib.title,
                                '<comment hidden>' if contrib.comment is None else contrib.comment,
                                ', '.join(contrib.tags if contrib.tags else ''))


    @staticmethod
    def get_blocks_for_user(wiki, user_name):
        """Returns an interable over TimelineEvents.

        """
        for block in wiki.get_user_blocks(user_name):
            if isinstance(block, BlockEvent):
                yield TimelineEvent(block.timestamp,
                                    block.target,
                                    'block',
                                    'reblock' if block.is_reblock else '',
                                    block.expiry or 'indef',
                                    '')
            elif isinstance(block, UnblockEvent):
                yield TimelineEvent(block.timestamp,
                                    block.target,
                                    'unblock',
                                    '',
                                    '',
                                    '')
            else:
                yield TimelineEvent(block.timestamp,
                                    block.target,
                                    'block',
                                    'unknown',
                                    '',
                                    '')

    @staticmethod
    def get_log_events_for_user(wiki, user_name):
        """Returns an iterable over TimelineEvents.

        """
        for event in wiki.get_user_log_events(user_name):
            yield TimelineEvent(event.timestamp,
                                event.user_name,
                                event.type,
                                event.action,
                                event.title,
                                '<comment hidden>' if event.comment is None else event.comment)


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
        socks = get_sock_names(wiki, case_name)
        sock_names = [s.username for s in socks if s.valid]

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
        return render(request, 'spi/g5.jinja', context)


    @staticmethod
    def g5_score(page):
        revisions = list(itertools.islice(page.revisions(), 50))
        if len(revisions) >= 50:
            return G5Score("unlikely", "50 or more revisions")
        editors = {r.user_name for r in revisions}
        if len(editors) == 1:
            return G5Score("likely", "only one editor")
        return G5Score("unknown")
