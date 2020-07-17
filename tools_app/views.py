from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import social_django.urls


def index(request):
    context = {}
    return render(request, 'tools_app/index.dtl', context)

@login_required()
def profile(request):
    context = {}
    return render(request, 'tools_app/profile.dtl', context)

def login_oauth(request):
    context = {}
    return render(request, 'tools_app/login.dtl', context)
