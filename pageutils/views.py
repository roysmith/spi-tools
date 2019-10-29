from django.shortcuts import render

SITE_NAME = 'en.wikipedia.org'


def index(request):
    context = {}
    return render(request, 'pageutils/index.dtl', context)
