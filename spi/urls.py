from django.urls import path, include
from spi.views import IndexView, IpAnalysisView, SockInfoView, SockSelectView, UserInfoView, TimecardView

urlpatterns = [
    path('', IndexView.as_view(), name="spi-index"),
    path('ip-analysis/<case_name>/', IpAnalysisView.as_view(), name="spi-ip-analysis"),
    path('spi-sock-info/<case_name>/', SockInfoView.as_view(), name="spi-sock-info"),
    path('spi-sock-select/<case_name>/', SockSelectView.as_view(), name="spi-sock-select"),
    path('spi-user-info/<user_name>/', UserInfoView.as_view(), name="spi-user-info"),
    path('spi-timecard/<case_name>', TimecardView.as_view(), name="spi-timecard"),
]
