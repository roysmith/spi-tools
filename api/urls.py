from django.urls import path
from api.views import CidrView

urlpatterns = [
    # pylint: disable=line-too-long
    path('cidr/', CidrView.as_view(), name="api-cidr"),
]
