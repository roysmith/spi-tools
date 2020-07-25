from django.urls import path, include
from .views import IndexView, IpAnalysisView, SockInfoView, SockSelectView, UserInfoView, TimecardView, UserActivitiesView, G5View

urlpatterns = [
    path('', IndexView.as_view(), name="spi-index"),
    path('ip-analysis/<case_name>/', IpAnalysisView.as_view(), name="spi-ip-analysis"),
    path('spi-sock-info/<case_name>/', SockInfoView.as_view(), name="spi-sock-info"),
    path('spi-sock-select/<case_name>/', SockSelectView.as_view(), name="spi-sock-select"),
    path('spi-user-info/<user_name>/', UserInfoView.as_view(), name="spi-user-info"),
    path('spi-user-activities/<user_name>', UserActivitiesView.as_view(), name="spi-user-activities"),
    path('spi-timecard/<case_name>', TimecardView.as_view(), name="spi-timecard"),
    path('spi-g5/<case_name>', G5View.as_view(), name="spi-g5"),
]
