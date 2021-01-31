"""tools_app URL Configuration"""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles import views as staticfile_views
from django.urls import include, path, re_path
from tools_app import views as tools_app_views
from spi import views as spi_views
import debug_toolbar

urlpatterns = [
    path('', spi_views.IndexView.as_view(), name='home'),
    path('account/logout', tools_app_views.logout, name='logout'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    path('cat_checker/', include('cat_checker.urls')),
    path('spi/', include('spi.urls')),
    path('pageutils/', include('pageutils.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'static/(?P<path>.*)', staticfile_views.serve),
        path('__debug__/', include(debug_toolbar.urls)),
    ]
