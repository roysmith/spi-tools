from django import forms

class CaseNameForm(forms.Form):
    case_name = forms.CharField(label='Case (sockmaster) name', max_length=100)
    use_archive = forms.BooleanField(label='Use archive?', required=False)

class IpRangeForm(forms.Form):
    first_ip = forms.CharField()
    last_ip = forms.CharField()

