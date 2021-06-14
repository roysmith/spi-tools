from django.urls import path
from spi.views import (IndexView,
                       IpAnalysisView,
                       SockSelectView,
                       TimecardView,
                       TimelineView,
                       G5View,
                       PagesView,
)

urlpatterns = [
    # pylint: disable=line-too-long
    path('', IndexView.as_view(), name="spi-index"),
    path('ip-analysis/<case_name>/', IpAnalysisView.as_view(), name="spi-ip-analysis"),
    path('sock-select/<case_name>/', SockSelectView.as_view(), name="spi-sock-select"),
    path('timecard/<case_name>', TimecardView.as_view(), name="spi-timecard"),
    path('timeline/<case_name>', TimelineView.as_view(), name="spi-timeline"),
    path('g5/<case_name>', G5View.as_view(), name="spi-g5"),
    path('pages/<case_name>', PagesView.as_view(), name="spi-pages"),
]
