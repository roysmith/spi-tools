from django.shortcuts import render
from mwclient import Site
from .forms import SummaryForm

def index(request):
    context = {}
    return render(request, 'spi/index.dtl', context)

def summary(request):
    if request.method == 'POST':
        form = SummaryForm(request.POST)
        if form.is_valid():
            master_name = form.cleaned_data['master_name']
            archive_page_title = 'Wikipedia:Sockpuppet investigations/%s/Archive' % master_name
            context = {'form': form,
                       'info': archive_page_title,
            }
            return render(request, 'spi/summary.dtl', context)
    else:
        form = SummaryForm()
    context = {'form': form} 
    return render(request, 'spi/summary.dtl', context)
