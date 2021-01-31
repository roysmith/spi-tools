from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
import django.contrib.auth
import social_django.urls

def logout(request):
    django.contrib.auth.logout(request)
    return redirect('home')
