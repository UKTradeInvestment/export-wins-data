from functools import wraps
from hashlib import sha256

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.crypto import constant_time_compare
from django.utils.decorators import available_attrs


def alice_exempt(view_func):
    """
    Marks a view function as being exempt from the alice view protection.
    """
    # We could just do view_func.alice_exempt = True, but decorators
    # are nicer if they don't have side-effects, so we return a new
    # function.
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    wrapped_view.alice_exempt = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


class SignatureRejectionMiddleware(object):
    """ Rejects requests that are not signed by a known server """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(view_func, 'alice_exempt', False):
            return None
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
