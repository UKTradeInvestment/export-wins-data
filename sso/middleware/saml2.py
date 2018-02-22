from django.contrib.auth import get_user
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

has_MI_permission = lambda _: False

class SSOAuthenticationMiddleware(MiddlewareMixin):
    """ SSO version of AuthenticationMiddleware
    """

    def authenticated(self, request):
        adfsuser = get_user(request)
        assert isinstance(adfsuser, (AnonymousUser,)), \
            'Incorrect User model'  # in case of problem with settins override
        return adfsuser and adfsuser.is_authenticated

    def process_request(self, request):
        request.mi_permission = request.session.get('_source', None) == 'oauth2'
        if not request.mi_permission and request.user.is_authenticated:
            request.mi_permission = has_MI_permission(request)
        return None
