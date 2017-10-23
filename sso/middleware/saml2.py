
import django
from django.test import override_settings
from django.contrib.auth.models import AnonymousUser

from sso.models import ADFSUser
from sso.views import get_user_attributes, has_MI_permission


class SSOAuthenticationMiddleware(object):
    """ SSO version of AuthenticationMiddleware

    Avoid using actual middleware since changing AUTHENTICATION_BACKENDS in
    settings causes problems with Export Wins, and also because this is a
    simple way to work around Django's dislike of supporting more than one
    User model by overriding AUTH_USER_MODEL in this one place

    """

    @override_settings(AUTH_USER_MODEL='sso.adfsuser')
    @override_settings(AUTHENTICATION_BACKENDS='djangosaml2.backends.Saml2Backend')
    def authenticated(self, request):
        adfsuser = django.contrib.auth.get_user(request)
        assert isinstance(adfsuser, (AnonymousUser, ADFSUser)), \
            'Incorrect User model'  # in case of problem with settins override
        return adfsuser and adfsuser.is_authenticated()

    def process_request(self, request):
        request.sso_authenticated = self.authenticated(request)
        request.mi_permission = False
        if request.sso_authenticated:
            request.adfs_attributes = get_user_attributes(request)
            request.mi_permission = has_MI_permission(request.adfs_attributes)
        return None
