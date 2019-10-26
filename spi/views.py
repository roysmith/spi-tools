from django.shortcuts import render
from mwclient import Site
import mwparserfromhell

from .forms import SummaryForm


SITE_NAME = 'en.wikipedia.org'


def index(request):
    context = {}
    return render(request, 'spi/index.dtl', context)


def summary(request):
    if request.method == 'POST':
        form = SummaryForm(request.POST)
        if form.is_valid():
            master_name = form.cleaned_data['master_name']
            archive_page_title = 'Wikipedia:Sockpuppet investigations/%s/Archive' % master_name
            context = {'form': form,
                       'info': _get_wikitext(archive_page_title),
            }
            return render(request, 'spi/summary.dtl', context)
    else:
        form = SummaryForm()
    context = {'form': form} 
    return render(request, 'spi/summary.dtl', context)


def _get_wikitext(page_title):
    site = Site(SITE_NAME)
    page = site.pages[page_title]
    return page.text()


class SPICase:
    def __init__(self, text):
        self.text = text
        self.code = mwparserfromhell.parse(text)

    def master_name(self):
        """Return the name of the sockmaster, parsed from a {{SPIarchive notice}}
        template.   Throws ValueError if there is not exactly one such template.
        """
        templates = self.code.filter_templates(
            matches = lambda n: n.name.matches('SPIarchive notice'))
        n = len(templates)
        if n ==  1:
            return templates[0].get('1').value
        raise ValueError("Found %d SPIarchive notices, expected exactly 1" % n)


    def socks(self):
        templates = self.code.filter_templates(
            matches = lambda n: n.name.matches('checkuser') or n.name.matches('checkIP'))
        return set(t.get('1').value.strip_code().strip() for t in templates)
