from django.urls import path, include
from spi import views

urlpatterns = [
    path('spi/', views.index, name="spi-index"),
]
