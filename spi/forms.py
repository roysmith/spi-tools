import urllib.parse

from django import forms
from django.core.exceptions import ValidationError

from wiki_interface import Wiki


class CaseNameChoiceField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def validate(self, value):
        if not value:
            raise ValidationError(self.error_messages['required'],
                                  code='required',
                                  params={'value': value})
        case_page_title = f'Wikipedia:Sockpuppet investigations/{value}'
        wiki = Wiki()
        if not wiki.page_exists(case_page_title):
            raise ValidationError(f'{case_page_title} does not exist.',
                                  code='invalid_choice',
                                  params={'value': value})


class CaseNameForm(forms.Form):
    case_name = CaseNameChoiceField()


class SockSelectForm(forms.Form):
    @staticmethod
    def build(sock_names):
        fields = {'sock_%s' % urllib.parse.quote(name):
                  forms.BooleanField(label=name, required=False)
                  for name in sock_names}
        sub_class = type('DynamicSockSelectForm', (SockSelectForm,), fields)

        return sub_class()


class UserInfoForm(forms.Form):
    count = forms.ChoiceField(choices=[(20, "20"),
                                       (50, "50"),
                                       (100, "100"),
                                       (250, "250"),
                                       (500, "500")])
    main = forms.BooleanField(required=False)
    draft = forms.BooleanField(required=False)
    other = forms.BooleanField(required=False)

    def clean(self):
        super().clean()
        data = self.cleaned_data
        if not (data.get("main") or data.get("draft") or data.get("other")):
            raise ValidationError(
                'At least one of "main", "draft", or "other" must be selected',
                code='no_ns')


class IpRangeForm(forms.Form):
    first_ip = forms.CharField()
    last_ip = forms.CharField()
