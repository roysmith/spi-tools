from django.urls import path, include
from spi import views

urlpatterns = [
    path('', views.index, name="spi-index"),
    path('ip-analysis/<case_name>/', views.ip_analysis, name="spi-ip-analysis"),
]
