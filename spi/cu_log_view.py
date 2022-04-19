import logging

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from wiki_interface import Wiki

logger = logging.getLogger('spi.views.cu_log_view')


class CuLogView(LoginRequiredMixin, View):
    def get(self, request):
        logger.info(request)
        wiki = Wiki(request)
        context = {'data': wiki.get_cu_log('Update202122'),
        }
        return render(request, 'spi/cu_log.html', context)
