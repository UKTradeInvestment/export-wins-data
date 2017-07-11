from django.conf import settings
from django.http import HttpResponseBadRequest
from django.middleware.security import SecurityMiddleware


class HttpsSecurityMiddleware(SecurityMiddleware):
    def process_request(self, request):
        """ Enforce https for all requests except when Debugging """
        if not settings.DEBUG and not request.is_secure():
            return HttpResponseBadRequest()
