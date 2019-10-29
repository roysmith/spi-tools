from django.urls import path, include
from cat_checker import views

urlpatterns = [
    # These should get moved to another app
    path('profile', views.profile, name='profile'),
    path('accounts/login', views.login_oauth, name='login'),
    path('oauth/', include('social_django.urls', namespace='social')),

    # These are the actual cat_checker routes
    path('', views.index),
    path('get_page_title/', views.get_page_title, name='get_page_title'),
]
