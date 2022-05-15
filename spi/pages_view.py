from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from spi.user_utils import CacheableUserContribs
from spi.spi_view import SpiView

# pylint: disable=invalid-name


logger = logging.getLogger('spi.views.pages_view')


class PagesView(LoginRequiredMixin, SpiView):
    def get(self, request, case_name):
        user_names = request.GET.getlist('users')
        logger.debug("user_names = %s", user_names)

        context = {'case_name': case_name,
                   'page_data': self.get_page_data(self.wiki, user_names)}
        return render(request, 'spi/pages.html', context)


    @dataclass(frozen=True)
    class PageData:
        edit_counts: Counter
        editor_counts: Counter
        reverted_counts: Counter


    @staticmethod
    def get_page_data(wiki, user_names):
        """Returns a PageData object.

        The keys for each counter will be the current page titles including the
        namespace (i.e.Talk:Foo).  The values will be:

        edit_counts: Total number of edits made to the page.
        editor_counts: Distinct editors who have edited the page
        reverted_counts: Number of edits to this page that have been reverted.

        Both active and deleted edits are included.

        Only edit_counts is guaranteed to have the full set of keys


        """
        edit_counts = Counter()
        editors = defaultdict(set)
        reverted = defaultdict(int)
        for user_name in user_names:
            contribs = list(itertools.chain(CacheableUserContribs.get(wiki, user_name).data,
                                            wiki.deleted_user_contributions(user_name)))
            edit_counts.update(c.title for c in contribs)
            for c in contribs:
                editors[c.title].add(user_name)
                if 'mw-reverted' in c.tags:
                    reverted[c.title] += 1
        editor_counts = Counter({k: len(v) for (k, v) in editors.items()})
        reverted_counts = Counter(reverted)
        return PagesView.PageData(edit_counts, editor_counts, reverted_counts)
