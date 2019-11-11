import logging

from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import constant_time_compare

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from mohawk import Receiver
from mohawk.exc import HawkFail

logger = logging.getLogger(__name__)

NO_CREDENTIALS_MESSAGE = 'Authentication credentials were not provided.'
INCORRECT_CREDENTIALS_MESSAGE = 'Incorrect authentication credentials.'
PAAS_ADDED_X_FORWARDED_FOR_IPS = 2


def _lookup_credentials(access_key_id):
    """Raises a HawkFail if the passed ID is not equal to
    settings.HAWK_ACCESS_KEY_ID
    """
    if not constant_time_compare(access_key_id, settings.HAWK_ACCESS_KEY_ID):
        raise HawkFail(f'No Hawk ID of {access_key_id}')

    return {
        'id': settings.HAWK_ACCESS_KEY_ID,
        'key': settings.HAWK_SECRET_ACCESS_KEY,
        'algorithm': 'sha256',
    }


def _seen_nonce(access_key_id, nonce, _):
    """Returns if the passed access_key_id/nonce combination has been
    used within settings.HAWK_NONCE_EXPIRY_SECONDS
    """
    cache_key = f'hawk:{access_key_id}:{nonce}'

    # cache.add only adds key if it isn't present
    seen_cache_key = not cache.add(
        cache_key, True, timeout=settings.HAWK_NONCE_EXPIRY_SECONDS,
    )

    if seen_cache_key:
        logger.warning(f'Already seen nonce {nonce}')

    return seen_cache_key


def _authorise(request):
    """Raises a HawkFail if the passed request cannot be authenticated"""
    return Receiver(
        _lookup_credentials,
        request.META['HTTP_AUTHORIZATION'],
        request.build_absolute_uri(),
        request.method,
        content=request.body,
        content_type=request.content_type,
        seen_nonce=_seen_nonce,
    )


class HawkAuthentication(BaseAuthentication):

    def authenticate_header(self, request):
        """This is returned as the WWW-Authenticate header when
        AuthenticationFailed is raised. DRF also requires this
        to send a 401 (as opposed to 403)
        """
        return 'Hawk'

    def authenticate(self, request):
        """Authenticates a request using two mechanisms:

        1. The X-Forwarded-For-Header, compared against a whitelist
        2. A Hawk signature in the Authorization header

        If either of these suggest we cannot authenticate, AuthenticationFailed
        is raised, as required in the DRF authentication flow
        """
        self._check_ip(request)
        return self._check_hawk_header(request)

    def _check_ip(self, request):
        """Blocks incoming connections based on IP in X-Forwarded-For

        Ideally, this would be done at the network level. However, this is
        not possible in PaaS. However, they do always add two IPs, with
        the first one being the IP connection are made from, so we can
        check the second-from-the-end with some confidence it hasn't been
        spoofed.

        This wouldn't be able to be trusted in other environments, but we're
        not running in non-PaaS environments in production.
        """

        if 'HTTP_X_FORWARDED_FOR' not in request.META:
            logger.warning(
                'Failed authentication: no X-Forwarded-For header passed'
            )
            raise AuthenticationFailed('Failed authentication: no X-Forwarded-For header passed')

        x_forwarded_for = request.META['HTTP_X_FORWARDED_FOR']
        ip_addesses = x_forwarded_for.split(',')

        if len(ip_addesses) < PAAS_ADDED_X_FORWARDED_FOR_IPS:
            logger.warning(
                'Failed authentication: the X-Forwarded-For header does not '
                'contain enough IP addresses'
            )
            raise AuthenticationFailed(
                'Failed authentication: the X-Forwarded-For header does not '
                'contain enough IP addresses'
            )

        remote_address = ip_addesses[-PAAS_ADDED_X_FORWARDED_FOR_IPS].strip()
        if remote_address not in settings.HAWK_IP_WHITELIST:
            logger.warning(
                'Failed authentication: the X-Forwarded-For header was not '
                'produced by a whitelisted IP'
            )
            raise AuthenticationFailed(
                'Failed authentication: the X-Forwarded-For header was not '
                'produced by a whitelisted IP\n\n'
                f'REMOTE ADDRESS: {remote_address}\nWHITELIST: {settings.HAWK_IP_WHITELIST}'
            )

    def _check_hawk_header(self, request):
        if 'HTTP_AUTHORIZATION' not in request.META:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE)

        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logger.warning('THEIR HASH: {}'.format(request.META['HTTP_AUTHORIZATION']))
            logger.warning(f'Failed authentication {e}')
            raise AuthenticationFailed(f'Failed authentication {e}')

        return (None, hawk_receiver)


class HawkResponseMiddleware:
    """Adds the Server-Authorization header to the response, so the originator
    of the request can authenticate the response
    """

    def process_response(self, viewset, response):
        """Adds the Server-Authorization header to the response, so the originator
        of the request can authenticate the response
        """
        response['Server-Authorization'] = viewset.request.auth.respond(
            content=response.content,
            content_type=response['Content-Type'],
        )
        return response