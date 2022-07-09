import logging
from datetime import datetime

logger = logging.getLogger('tools_app.middleware')

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = datetime.utcnow()
        response = self.get_response(request)
        dt = datetime.utcnow() - t0
        logger.info("request took %s", dt)
        return response


    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    def process_view(self, request, view_func, view_args, view_kwargs):
        logger.info("%s()", view_func.__qualname__)


# pylint: disable=too-few-public-methods
class RequestAugmentationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.x_tools_request_time_utc = datetime.utcnow()
        return self.get_response(request)
