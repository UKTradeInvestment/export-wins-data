from hashlib import sha256

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.crypto import constant_time_compare


class SignatureRejectionMiddleware(object):
    """ Rejects requests that are not signed by a known server """

    def process_request(self, request):
        if not self._test_signature(request):
            if settings.DEBUG and settings.API_DEBUG:
                pass
            else:
                return HttpResponseBadRequest("PFO")
        return None

    def _generate_signature(self, secret, path, body):
        salt = bytes(secret, "utf-8")
        path = bytes(path, "utf-8")
        return sha256(path + body + salt).hexdigest()

    def _test_signature(self, request):
        """ Return True/False if the signature is recognized

        Note, we accept from UI server, admin server and MI server.

        Note, we set the `server_name` attribute of the matched server on
        request for permission management.

        """
        offered = request.META.get("HTTP_X_SIGNATURE")
        if not offered:
            return False

        # check each server secret for a match
        servers = [
            (settings.UI_SECRET, 'ui'),
            (settings.ADMIN_SECRET, 'admin'),
            (settings.MI_SECRET, 'mi'),
            (settings.DATA_SECRET, 'data')
        ]
        for secret, server_name in servers:
            generated = self._generate_signature(
                secret,
                request.get_full_path(),
                request.body,
            )
            if constant_time_compare(generated, offered):
                request.server_name = server_name
                return True
