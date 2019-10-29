from django.urls import path, include
from pageutils import views

urlpatterns = [
    path('', views.index, name="pageutils-index"),
]
