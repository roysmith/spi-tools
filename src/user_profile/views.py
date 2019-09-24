from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from .forms import CheckRefForm

def index(request):
    context = {}
    return render(request, 'user_profile/index.dtl', context)

@login_required()
def profile(request):
    context = {}
    return render(request, 'user_profile/profile.dtl', context)

def login_oauth(request):
    context = {}
    return render(request, 'user_profile/login.dtl', context)

def check_refs(request):
    if request.method == 'POST':
        form = CheckRefForm(request.POST)
        if form.is_valid():
            context = {
                'title': form.cleaned_data['page_title'],
                }
            return render(request, 'user_profile/page_title.dtl', context)
    else:
        form = CheckRefForm()

    context = {
        'form': form,
        }
    return render(request, 'user_profile/check_refs.dtl', context)

def page_title(request):
    context = {
        'page_title': 'xxx',
        }
    return render(request, 'user_profile/page_title.dtl', context)

    
    
    
