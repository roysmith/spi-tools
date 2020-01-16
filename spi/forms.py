from django import forms
from django.core.exceptions import ValidationError
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


class SelectizeField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, value):
        if not value:
            raise ValidationError(self.error_messages['required'],
                                  code='required',
                                  params={'value': value})
        case_page_title = f'Wikipedia:Sockpuppet investigations/{value}'
        site = Site(SITE_NAME)
        if not site.pages[case_page_title].text():
            raise ValidationError(f'{case_page_title} does not exist.',
                                  code='invalid_choice',
                                  params={'value': value})

class CaseNameForm(forms.Form):
    case_name = SelectizeField(label='Case (sockmaster) name',
                                     choices=get_current_case_names())
    use_archive = forms.BooleanField(label='Use archive?',
                                     required=False)


class IpRangeForm(forms.Form):
    first_ip = forms.CharField()
    last_ip = forms.CharField()

