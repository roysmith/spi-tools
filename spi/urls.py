from django.urls import path
from spi.views import (IndexView, IpAnalysisView, SockInfoView, SockSelectView,
                       UserInfoView, TimecardView, TimelineView, UserActivitiesView, G5View)

urlpatterns = [
    # pylint: disable=line-too-long
    path('', IndexView.as_view(), name="spi-index"),
    path('ip-analysis/<case_name>/', IpAnalysisView.as_view(), name="spi-ip-analysis"),
    path('sock-info/<case_name>/', SockInfoView.as_view(), name="spi-sock-info"),
    path('sock-select/<case_name>/', SockSelectView.as_view(), name="spi-sock-select"),
    path('user-info/<user_name>/', UserInfoView.as_view(), name="spi-user-info"),
    path('user-activities/<user_name>', UserActivitiesView.as_view(), name="spi-user-activities"),
    path('timecard/<case_name>', TimecardView.as_view(), name="spi-timecard"),
    path('timeline/<case_name>', TimelineView.as_view(), name="spi-timeline"),
    path('g5/<case_name>', G5View.as_view(), name="spi-g5"),
]
