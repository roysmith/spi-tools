import urllib.parse

from django import forms


class SearchForm(forms.Form):
    search_terms = forms.CharField()
