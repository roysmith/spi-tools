from django import forms

class GetPageTitleForm(forms.Form):
    page_title = forms.CharField(label='Page Title', max_length=100)
