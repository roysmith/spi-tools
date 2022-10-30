from functools import partial
import logging

from django.shortcuts import render, redirect
from django.urls import reverse

from spi import icache as cache
from spi.forms import CaseNameForm
from spi.cu_log_view import CuLogView
from spi.spi_utils import get_current_case_names
from spi.spi_view import SpiView


logger = logging.getLogger('spi.views.index_view')


class IndexView(SpiView):
    def get(self, request):
        form = CaseNameForm(wiki=self.wiki)
        case_name = request.GET.get('caseName')
        context = {'form': form,
                   'choices': self.generate_select2_data(case_name=case_name, wiki=self.wiki),
                   'do_checkuser': CuLogView.is_authorized(request, self.wiki),
                   }
        return render(request, 'spi/index.html', context)

    def post(self, request):
        form = CaseNameForm(request.POST, wiki=self.wiki)
        context = {'form': form,
                   'choices': self.generate_select2_data(wiki=self.wiki)
                   }
        if form.is_valid():
            case_name = form.cleaned_data['case_name']
            if 'ip-info-button' in request.POST:
                return redirect('spi-ip-analysis', case_name)
            if 'sock-select-button' in request.POST:
                return redirect('%s' % (reverse('spi-sock-select', args=[case_name])))
            if 'g5-button' in request.POST:
                return redirect('%s' % (reverse('spi-g5', args=[case_name])))
            if 'cu-log-button' in request.POST:
                return redirect('spi-cu-log', case_name)
            message = 'No known button in POST (%s)' % request.POST.keys()
            logger.error(message)
            context['error'] = message

        return render(request, 'spi/index.html', context)

    @staticmethod
    def generate_select2_data(case_name=None, *, wiki):
        """Return data appropriate for the 'data' element of a select2.js
        configuration object.

        If case_name is provided, that option has the "selected"
        attribute set.  If it doesn't exist in the default list, it is
        added (and selected).

        """
        names = cache.get_or_set('IndexView.case_names',
                                 partial(get_current_case_names, wiki),
                                 300)
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
