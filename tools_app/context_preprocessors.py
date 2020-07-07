import datetime
from django.conf import settings

def debug(request):
    return {'VERSION_ID': settings.VERSION_ID,
            'REQUEST_TIME': str(datetime.datetime.now(datetime.timezone.utc)),
    }
