"""tools_app URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from spi import views as spi_views

urlpatterns = [
    path('', spi_views.index), # temporary
    path('admin/', admin.site.urls),
    path('cat_checker/', include('cat_checker.urls')),
    path('spi/', include('spi.urls')),
]
