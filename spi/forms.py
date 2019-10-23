from django import forms

class SummaryForm(forms.Form):
    master_name = forms.CharField(label='Sockmaster name', max_length=100)
