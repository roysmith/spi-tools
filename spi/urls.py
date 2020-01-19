from django.urls import path, include
from spi.views import IndexView, IpAnalysisView, SockInfoView, UserInfoView

urlpatterns = [
    path('', IndexView.as_view(), name="spi-index"),
    path('ip-analysis/<case_name>/', IpAnalysisView.as_view(), name="spi-ip-analysis"),
    path('spi-sock-info/<case_name>/', SockInfoView.as_view(), name="spi-sock-info"),
    path('spi-user-info/<user_name>/', UserInfoView.as_view(), name="spi-user-info"),
]
