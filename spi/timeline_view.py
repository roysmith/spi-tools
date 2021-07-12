from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import heapq
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from spi.user_utils import CacheableUserContribs
from wiki_interface import Wiki
from wiki_interface.block_utils import BlockEvent, UnblockEvent


logger = logging.getLogger('spi.views.timeline_view')


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

        self.tag_data = {}  # pylint: disable=attribute-defined-outside-init
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
        return render(request, 'spi/timeline.html', context)


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
        active = CacheableUserContribs.get(wiki, user_name).data
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
        for block in wiki.user_blocks(user_name):
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
        for event in wiki.user_log_events(user_name):
            yield TimelineEvent(event.timestamp,
                                event.user_name,
                                event.type,
                                event.action,
                                event.title,
                                '<comment hidden>' if event.comment is None else event.comment)
