from django.urls import path
from search.views import IndexView

urlpatterns = [
    # pylint: disable=line-too-long
    path('', IndexView.as_view(), name="search-index"),
]
