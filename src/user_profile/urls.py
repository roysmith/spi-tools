from django.urls import path, include
from user_profile import views

urlpatterns = [
    path('profile', views.profile, name='profile'),
    path('accounts/login', views.login_oauth, name='login'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('check_refs', views.check_refs, name='check_refs'),
    path('', views.index),
]
