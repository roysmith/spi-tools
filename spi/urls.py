from django.urls import path
from spi.index_view import IndexView
from spi.ip_analysis_view import IpAnalysisView
from spi.sock_select_view import SockSelectView
from spi.timecard_view import TimecardView
from spi.timeline_view import TimelineView
from spi.pages_view import PagesView
from spi.g5_view import G5View

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
