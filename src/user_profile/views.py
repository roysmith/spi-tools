from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from .forms import GetPageTitleForm

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

def get_page_title(request):
    if request.method == 'POST':
        form = GetPageTitleForm(request.POST)
        if form.is_valid():
            context = {'title': form.cleaned_data['page_title']}
            return render(request, 'user_profile/page_title.dtl', context)
    else:
        form = GetPageTitleForm()
    context = {'form': form} 
    return render(request, 'user_profile/get_page_title.dtl', context)

