from datetime import datetime
import logging
import urllib

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from spi.forms import SockSelectForm
from spi.views import get_sock_names
from wiki_interface import Wiki


logger = logging.getLogger('spi.views.sock_select_view')

EDITOR_INTERACT_BASE = "https://tools.wmflabs.org/sigma/editorinteract.py"


class SockSelectView(View):
    def get(self, request, case_name):
        wiki = Wiki()
        user_infos = list(get_sock_names(wiki, case_name))
        logger.debug(user_infos)
        users_by_name = {user.username: user for user in user_infos}
        names = list({user.username for user in user_infos if user.valid})
        invalid_users = [user for user in user_infos if not user.valid]
        dates = [users_by_name[name].date for name in names]
        form = SockSelectForm.build(names)

        all_date_strings = set(user.date for user in user_infos if user.date)
        keyed_dates = [(datetime.strptime(d, '%d %B %Y'), d) for d in all_date_strings]

        context = {'case_name': case_name,
                   'form_info': list(zip(form, names, dates)),
                   'invalid_users': invalid_users,
                   'dates': [v for (k, v) in sorted(keyed_dates, reverse=True)]}
        return render(request, 'spi/sock-select.html', context)


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

            if 'pages-button' in request.POST:
                url = '%s?%s' % (reverse("spi-pages", args=[case_name]),
                                 self.get_encoded_users(request))
                return redirect(url)

            logger.error("Unknown button!")

        logger.debug("post: not valid")
        context = {'case_name': case_name,
                   'form': form}
        return render(request, 'spi/sock-select.html', context)


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
