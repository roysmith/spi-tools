from django.urls import path, include
from cat_checker import views

urlpatterns = [
    # These are the actual cat_checker routes
    path('', views.index),
    path('get_page_title/', views.get_page_title, name='get_page_title'),
]
