import logging
import datetime

logger = logging.getLogger('view')

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        logger.info("%s()", view_func.__qualname__)


class RequestAugmentationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.x_tools_request_time_utc = datetime.datetime.utcnow()
        return self.get_response(request)
