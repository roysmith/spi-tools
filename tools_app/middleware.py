import logging

logger = logging.getLogger('view')

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        logger.info("%s()", view_func.__qualname__)
