import logging
import datetime

logger = logging.getLogger('tools_app.middleware')

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    def process_view(self, request, view_func, view_args, view_kwargs):
        logger.info("%s()", view_func.__qualname__)


# pylint: disable=too-few-public-methods
class RequestAugmentationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.x_tools_request_time_utc = datetime.datetime.utcnow()
        return self.get_response(request)
