from django.shortcuts import render
from mwclient import Site

def index(request):
    context = {}
    return render(request, 'spi/index.dtl', context)
