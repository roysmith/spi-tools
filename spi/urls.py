from django.urls import path, include
from spi import views

urlpatterns = [
    path('', views.index, name="spi-index"),
    path('summary/<case_name>/', views.summary, name="spi-summary"),
]
