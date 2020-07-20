from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import django.contrib.auth
import social_django.urls


def login_oauth(request):
    context = {}
    return render(request, 'tools_app/login.dtl', context)

def logout(request):
    django.contrib.auth.logout(request)
    return redirect('home')

