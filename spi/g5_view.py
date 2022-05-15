from dataclasses import dataclass
import datetime
import itertools
import logging

from django.shortcuts import render

from spi.spi_view import get_sock_names, SpiView
from wiki_interface import Wiki
from wiki_interface.block_utils import UserBlockHistory



logger = logging.getLogger('spi.views.g5_view')


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


class G5View(SpiView):
    def get(self, request, case_name):
        socks = get_sock_names(self.wiki, case_name)
        sock_names = [s.username for s in socks if s.valid]

        history = UserBlockHistory(self.wiki.user_blocks(case_name))

        page_creations = []
        for contrib in self.wiki.user_contributions(sock_names, show="new"):
            if history.is_blocked_at(contrib.timestamp):
                title = contrib.title
                page = self.wiki.page(title)
                if page.exists():
                    page_creations.append(G5Summary(title,
                                                    contrib.user_name,
                                                    contrib.timestamp,
                                                    self.g5_score(page)))

        context = {'case_name': case_name,
                   'page_creations': page_creations,
                   }
        return render(request, 'spi/g5.html', context)


    @staticmethod
    def g5_score(page):
        revisions = list(itertools.islice(page.revisions(), 50))
        if len(revisions) >= 50:
            return G5Score("unlikely", "50 or more revisions")
        editors = {r.user_name for r in revisions}
        if len(editors) == 1:
            return G5Score("likely", "only one editor")
        return G5Score("unknown")
