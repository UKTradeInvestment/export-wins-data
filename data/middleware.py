from django.http import HttpResponseForbidden, HttpResponsePermanentRedirect
from django.middleware.security import SecurityMiddleware


class HttpsSecurityMiddleware(SecurityMiddleware):
    def process_request(self, request):
        if not request.is_secure:
            return HttpResponseForbidden()
        path = request.path.lstrip("/")
        if (self.redirect and not request.is_secure() and
                not any(pattern.search(path)
                        for pattern in self.redirect_exempt)):
            host = self.redirect_host or request.get_host()
            return HttpResponsePermanentRedirect(
                "https://%s%s" % (host, request.get_full_path())
            )