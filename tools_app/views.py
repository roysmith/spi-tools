import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import social_django.urls

logger = logging.getLogger('view')

def index(request):
    logger.debug("tools_app.index()")
    context = {}
    return render(request, 'tools_app/index.dtl', context)

@login_required()
def profile(request):
    logger.debug("tools_app.profile()")
    context = {}
    return render(request, 'tools_app/profile.dtl', context)

def login_oauth(request):
    logger.debug("tools_app.login_oauth()")
    logger.debug("social_django.urls.urlpatterns = %s" % str(social_django.urls.urlpatterns))
    context = {}
    return render(request, 'tools_app/login.dtl', context)
