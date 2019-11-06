from django.urls import path, include
from spi.views import IndexView, IpAnalysisView

urlpatterns = [
    path('', IndexView.as_view(), name="spi-index"),
    path('ip-analysis/<case_name>/', IpAnalysisView.as_view(), name="spi-ip-analysis"),
]
