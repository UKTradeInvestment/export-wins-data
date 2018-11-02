import logging

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.middleware.security import SecurityMiddleware

logger = logging.getLogger(__name__)


class HttpsSecurityMiddleware(SecurityMiddleware):
    def process_request(self, request):
        """ Enforce https for all requests except when Debugging """
        if not settings.DEBUG and not request.is_secure():
            return HttpResponseBadRequest()


class RequestLoggerMiddleware:
    """Middleware that performs request logging for auditing purpose."""

    def __init__(self, get_response=None):
        """Initialise the request logger middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request and log the data."""
        response = self.get_response(request)

        data = self._gather_request_data(request, response)
        logger.info('request', extra=data)
        return response

    def _gather_request_data(self, request, response):
        """Gather request data."""
        data = {
            'method': request.method,
            'path': request.get_full_path(),
            'status_code': response.status_code,
            'sso_user_id': getattr(request.user, 'sso_user_id', None),
            'local_user_id': getattr(request.user, 'id', None),
        }
        return data
