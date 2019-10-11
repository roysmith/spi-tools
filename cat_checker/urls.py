from django.urls import path, include
from cat_checker import views

urlpatterns = [
    path('profile', views.profile, name='profile'),
    path('accounts/login', views.login_oauth, name='login'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('get_page_title', views.get_page_title, name='get_page_title'),
    path('', views.index),
]
