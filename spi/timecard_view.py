import logging
import requests


from django.shortcuts import render
from django.views import View
from wiki_interface import Wiki  #pylint: disable=unused-import


logger = logging.getLogger('spi.views.timecard_view')

TIMECARD_BASE = 'https://xtools.wmflabs.org/api/user/timecard/en.wikipedia.org'


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
        return render(request, 'spi/timecard.html', context)
