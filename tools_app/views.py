from django.shortcuts import redirect
import django.contrib.auth

def logout(request):
    django.contrib.auth.logout(request)
    return redirect('home')
