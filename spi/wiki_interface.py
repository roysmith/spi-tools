"""A high-level programatic interface to the wiki.

This sits on top of mwclient.Site and provides a higher level
abstraction.  Sets of values are passed as iterators instead of piped
strings.  Times are represented as datetimes instead of struct_times.
Future functionality may include caching.

All wiki access should go through this layer.  Do not use
mwclient.Site directly.

"""
import logging
import datetime
from dataclasses import dataclass

import django.contrib.auth
from django.conf import settings
from mwclient import Site
from mwclient.listing import List
from mwclient.errors import APIError
from dateutil.parser import isoparse
import mwparserfromhell

from .spi_utils import SpiSourceDocument, SpiCase
from .block_utils import BlockEvent, UnblockEvent
from .time_utils import struct_to_datetime


logger = logging.getLogger('spi.wiki_interface')


@dataclass(frozen=True, order=True)
class WikiContrib:
    timestamp: datetime.datetime
    user_name: str
    title: str
    comment: str
    is_live: bool = True


class Wiki:
    """High-level wiki interface.

    This knows about user credentials, so you must Create a new
    instance of this for every request.

    """
    def __init__(self, request=None):
        self.site = self.get_mw_site(request)


    @staticmethod
    def get_mw_site(request):
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


    def get_current_case_names(self):
        """Return an list of the currently active SPI case names as strings.

        """
        overview = self.site.pages['Wikipedia:Sockpuppet investigations/Cases/Overview'].text()
        wikicode = mwparserfromhell.parse(overview)
        templates = wikicode.filter_templates(matches=lambda n: n.name.matches('SPIstatusentry'))
        return [str(t.get(1)) for t in templates]


    def page_exists(self, title):
        """Return True if the page exists, False otherwise."""

        return self.site.pages[title].exists


    def get_case_ips(self, case_name):
        """Get all the IP addresses which have been mentioned
        in a SPI case.

        Returns a iterable over SpiIpInfos

        """
        case_title = 'Wikipedia:Sockpuppet investigations/%s' % case_name
        archive_title = '%s/Archive' % case_title

        case_doc = SpiSourceDocument(case_title, self.site.pages[case_title].text())
        docs = [case_doc]

        archive_text = self.site.pages[archive_title].text()
        if archive_text:
            archive_doc = SpiSourceDocument(archive_title, archive_text)
            docs.append(archive_doc)

        case = SpiCase(*docs)
        return case.find_all_ips()



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


    def get_case(self, master_name, use_archive=True):
        """Returns a SpiCase.

        If use_archive is true, both the current case and any existing
        archive is used.  Otherwise, just the current case.

        """
        case_title = 'Wikipedia:Sockpuppet investigations/%s' % master_name
        archive_title = '%s/Archive' % case_title

        case_doc = SpiSourceDocument(case_title, self.site.pages[case_title].text())
        docs = [case_doc]

        archive_text = use_archive and self.site.pages[archive_title].text()
        if archive_text:
            archive_doc = SpiSourceDocument(archive_title, archive_text)
            docs.append(archive_doc)

        return SpiCase(*docs)


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
        names = [user_name_or_names] if isinstance(user_name_or_names, str) else user_name_or_names
        all_names = []
        for name in names:
            str_name = str(name)
            if '|' in str_name:
                raise ValueError(f'"|" in user name: {str_name}')
            all_names.append(str_name)

        for contrib in self.site.usercontributions('|'.join(all_names), show=show):
            logger.info('==> %s', contrib)
            yield WikiContrib(struct_to_datetime(contrib['timestamp']),
                              contrib['user'],
                              contrib['title'],
                              contrib['comment'])


    def deleted_user_contributions(self, user_name):
        """Get a user's deleted edits.

        Returns an interable over WikiContribs.

        If the mwclient connection is not authenticated to a
        user with admin rights, returns an empty iterable.

        """
        kwargs = dict(List.generate_kwargs('adr', user=user_name))
        listing = List(self.site,
                       'alldeletedrevisions',
                       'adr',
                       uselang=None,  # unclear why this is needed
                       **kwargs)

        # See https://www.mediawiki.org/wiki/API:Alldeletedrevisions#Response; this is
        # iterating over response['query']['alldeletedrevisions'].
        try:
            for page in listing:
                title = page['title']
                for revision in page['revisions']:
                    logger.debug("deleted revision = %s", revision)
                    timestamp = isoparse(revision['timestamp'])
                    title = page['title']
                    comment = revision['comment']
                    yield WikiContrib(timestamp, user_name, title, comment, is_live=False)
        except APIError as ex:
            if ex.args[0] == 'permissiondenied':
                logger.warning('Permission denied in wiki_interface.deleted_user_contributions()')
                # We're assuming that the exception will be raised
                # before any data is returned.  There's probably some
                # edge cases where data is returned in multiple chunks
                # and the permission is lost between chunks.  At
                # worst, this should result in incompplete data being
                # returned, but that's not 100% clear.
                return
            raise



    def get_user_blocks(self, user_name):
        """Get the user's block history.

        Returns a (heterogeneous) list of BlockEvents and
        UnblockEvents in chronological order (i.e. oldest first).

        """
        blocks = self.site.logevents(title=f'User:{user_name}', type="block", dir="newer")
        events = []
        for block in blocks:
            action = block['action']
            timestamp = struct_to_datetime(block['timestamp'])
            mw_expiry = block['params'].get('expiry')
            expiry = mw_expiry and isoparse(mw_expiry)
            if action == 'block':
                events.append(BlockEvent(user_name, timestamp, expiry))
            if action == 'reblock':
                events.append(BlockEvent(user_name, timestamp, expiry, reblock=True))
            if action == 'unblock':
                events.append(UnblockEvent(user_name, timestamp))
            else:
                logger.error('Ignoring block due to unknown block action in %s', block)
        return events
