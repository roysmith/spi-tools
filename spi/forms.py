from django import forms
from mwclient import Site
import mwparserfromhell

SITE_NAME = 'en.wikipedia.org'

def get_current_case_names():
    site = Site(SITE_NAME)
    overview = site.pages['Wikipedia:Sockpuppet investigations/Cases/Overview'].text()
    wikicode = mwparserfromhell.parse(overview)
    templates = wikicode.filter_templates(
        matches = lambda n: n.name.matches('SPIstatusentry'))
    choices = [(str(t.get(1)), str(t.get(1))) for t in templates]
    return choices


class CaseNameForm(forms.Form):
    current_cases = forms.ChoiceField(choices=get_current_case_names(),
                                      label='Case name preloads')
    case_name = forms.CharField(label='Case (sockmaster) name')
    use_archive = forms.BooleanField(label='Use archive?', required=False)

class IpRangeForm(forms.Form):
    first_ip = forms.CharField()
    last_ip = forms.CharField()

