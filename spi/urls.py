from django.urls import path, include
from spi import views

urlpatterns = [
    path('', views.index, name="spi-index"),
    path('summary/', views.summary, name="spi-summary"),
]
