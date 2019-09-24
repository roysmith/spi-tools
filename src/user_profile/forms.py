from django import forms

class CheckRefForm(forms.Form):
    page_title = forms.CharField(label='Page Title', max_length=100)
