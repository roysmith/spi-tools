from django import forms

class CaseNameForm(forms.Form):
    case_name = forms.CharField(label='Case (sockmaster) name', max_length=100)
