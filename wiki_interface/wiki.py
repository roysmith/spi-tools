"""A high-level programatic interface to the wiki.

This sits on top of mwclient.Site and provides a higher level
abstraction.  Sets of values are passed as iterators instead of piped
strings.  Times are represented as datetimes instead of struct_times.
Future functionality may include caching.

All wiki access should go through this layer.  Do not use
mwclient.Site directly.

"""
import logging
from dataclasses import dataclass
from itertools import islice

import django.contrib.auth
from django.conf import settings
from mwclient import Site
from mwclient.listing import List
from mwclient.errors import APIError
import mwclient
from dateutil.parser import isoparse
from more_itertools import always_iterable, chunked, consume

from wiki_interface.data import WikiContrib, LogEvent
from wiki_interface.block_utils import BlockEvent, UnblockEvent
from wiki_interface.time_utils import struct_to_datetime


logger = logging.getLogger('wiki_interface')


class Wiki:
    """High-level wiki interface.

    This knows about user credentials, so you must Create a new
    instance of this for every request.

    """
    def __init__(self, request=None):
        self.site = self._get_mw_site(request)
        self.namespaces = self.site.namespaces
        self.namespace_values = {v: k for k, v in self.namespaces.items()}


    @staticmethod
    def _get_mw_site(request):
        user = request and django.contrib.auth.get_user(request)

        # It's not clear if we need to bother checking to see if the user
        # is authenticated.  Maybe with an AnonymousUser, everything just
        # works?  If so, these two code paths could be merged.
        if user is None or user.is_anonymous:
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


    def page_exists(self, title):
        """Return True if the page exists, False otherwise."""

        return self.site.pages[title].exists


    def get_registration_time(self, user):
        """Return the registration time for a user as a string.

        If the registration time can't be determined, returns None.

        """
        registrations = self.site.users(users=[user], prop=['registration'])
        userinfo = registrations.next()
        try:
            return userinfo['registration']
        except KeyError:
            return None


    # See https://www.mediawiki.org/wiki/API:Usercontribs.
    MAX_UCUSER = 50

    def user_contributions(self, user_name_or_names, show=''):
        """Get one or more users' live (i.e. non-deleted) edits.

        If user_name_or_names is a string, get the edits for that
        user.  Otherwise, it's an iterable over strings, representing
        a set of users.  The contributions for all of the users are
        returned.

        Little Bobby Tables alert: As a temporary hack, it is a
        ValueError for any of the names to contain a pipe ('|')
        character.

        Returns an iterable over WikiContribs.

        """
        all_names = []
        for name in always_iterable(user_name_or_names):
            str_name = str(name)
            if '|' in str_name:
                raise ValueError(f'"|" in user name: {str_name}')
            all_names.append(str_name)

        props = 'title|timestamp|comment|flags|tags'
        for chunk in chunked(all_names, self.MAX_UCUSER):
            for contrib in self.site.usercontributions('|'.join(chunk), show=show, prop=props):
                logger.debug("contrib = %s", contrib)
                yield WikiContrib(struct_to_datetime(contrib['timestamp']),
                                  contrib['user'],
                                  contrib['ns'],
                                  contrib['title'],
                                  contrib['comment'] if 'commenthidden' not in contrib else None,
                                  True,
                                  contrib['tags'])


    def deleted_user_contributions(self, user_name):
        """Get a user's deleted edits.

        Returns an interable over WikiContribs.

        If the mwclient connection is not authenticated to a
        user with admin rights, returns an empty iterable.

        The current implementation stores and sorts all the
        WikiContribs internally.  It may be possible to avoid this
        in-memory storage using a merge sort, but it would be messy,
        and probably not worth the effort, as the expected number of
        deleted contributions is small.

        """
        kwargs = dict(List.generate_kwargs('adr',
                                           user=user_name,
                                           prop='title|timestamp|comment|flags|tags'))
        listing = List(self.site,
                       'alldeletedrevisions',
                       'adr',
                       uselang=None,  # unclear why this is needed
                       **kwargs)

        # See https://www.mediawiki.org/wiki/API:Alldeletedrevisions#Response; this is
        # iterating over response['query']['alldeletedrevisions'].
        contribs = []
        try:
            for page in listing:
                title = page['title']
                namespace = page['ns']
                for revision in page['revisions']:
                    logger.debug("deleted revision = %s", revision)
                    timestamp = isoparse(revision['timestamp'])
                    comment = revision['comment'] if 'commenthidden' not in revision else None
                    tags = revision['tags']
                    contribs.append(WikiContrib(
                        timestamp, user_name, namespace, title, comment, is_live=False, tags=tags))
        except APIError as ex:
            if ex.args[0] == 'permissiondenied':
                logger.warning('Permission denied in wiki_interface.deleted_user_contributions()')
                # We're assuming that the exception will be raised
                # before any data is returned.  There's probably some
                # edge cases where data is returned in multiple chunks
                # and the permission is lost between chunks.  At
                # worst, this should result in incompplete data being
                # returned, but that's not 100% clear.
                return []
            raise
        contribs.sort(reverse=True)
        return contribs


    def get_user_blocks(self, user_name):
        """Get the user's block history.

        Returns a (heterogeneous) list of BlockEvents and
        UnblockEvents.

        Events are returned in reverse chronological order
        (i.e. most recent first).
        """
        blocks = self.site.logevents(title=f'User:{user_name}', type="block")
        events = []
        for block in blocks:
            action = block['action']
            timestamp = struct_to_datetime(block['timestamp'])
            mw_expiry = block['params'].get('expiry')
            expiry = mw_expiry and isoparse(mw_expiry)
            if action == 'block':
                events.append(BlockEvent(user_name, timestamp, expiry))
            elif action == 'reblock':
                events.append(BlockEvent(user_name, timestamp, expiry, is_reblock=True))
            elif action == 'unblock':
                events.append(UnblockEvent(user_name, timestamp))
            else:
                logger.error('Ignoring block due to unknown block action in %s', block)
        return events



    def get_user_log_events(self, user_name):
        """Get the user's log events, i.e. where the user is the performer.
        Things that happened *to* the user are accessed through other
        calls, such as get_user_blocks().

        Returns an iterable over LogEvents.

        """
        for event in self.site.logevents(user=user_name):
            yield LogEvent(struct_to_datetime(event['timestamp']),
                           event['user'],
                           event['title'],
                           event['type'],
                           event['action'],
                           event['comment'] if 'commenthidden' not in event else None)

    def page(self, title):
        return Page(self, title)


    def is_valid_username(self, user_name):
        """Test a username for validity.  Valid in this context means properly
        formed, i.e. the underlying API doesn't return a 'baduser'
        error.  It is possible (common, even), for a username to be
        valid but not exist on a particular wiki.

        Returns True for valid usernames, False for invalid usernames.

        """
        try:
            consume(islice(self.site.usercontributions(user_name, limit=1), 0, 1))
            return True
        except APIError as ex:
            if ex.code == 'baduser':
                return False
            raise


@dataclass
class Page:
    wiki: Wiki
    mw_page: mwclient.page.Page


    def __init__(self, wiki, title):
        self.wiki = wiki
        self.mw_page = self.wiki.site.pages[title]


    def exists(self):
        return self.mw_page.exists


    def revisions(self):
        for rev in self.mw_page.revisions():
            comment = rev['comment'] if 'commenthidden' not in rev else None
            yield WikiContrib(struct_to_datetime(rev['timestamp']),
                              rev['user'],
                              self.mw_page.namespace,
                              self.mw_page.name,
                              comment)

    def text(self):
        return self.mw_page.text()
