import datetime
from django.conf import settings

def debug(request):
    request_start_time = request.x_tools_request_time_utc
    server_start_time = settings.SERVER_START_TIME_UTC
    now = datetime.datetime.utcnow()
    request_duration = round((now - request_start_time).total_seconds(), 3)
    uptime = now - server_start_time
    if settings.DEBUG:
        production_host_name = request.get_host().replace('-dev', '')
    else:
        production_host_name = None


    return {'VERSION_ID': settings.VERSION_ID,
            'DEBUG_ENABLED': settings.DEBUG,
            'REQUEST_START_TIME_UTC': request_start_time.isoformat(timespec="seconds"),
            'REQUEST_DURATION': request_duration,
            'SERVER_START_TIME_UTC': server_start_time.isoformat(timespec="seconds"),
            'SERVER_UP_TIME': datetime.timedelta(seconds = int(uptime.total_seconds())),
            'PRODUCTION_HOST_NAME': production_host_name,
    }
