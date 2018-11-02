from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now, make_aware
from requests_oauthlib import OAuth2Session

has_MI_permission = False

class OAuth2IntrospectToken(MiddlewareMixin):
    """
    Token introspection middleware for OAuth2 version of SSO
    """

    def process_request(self, request):
        client = OAuth2Session(
            client_id=settings.OAUTH2_CLIENT_ID,
            token={'access_token': settings.OAUTH2_INTROSPECT_TOKEN,
                   'token_type': 'Bearer'},
        )
        source = request.session.get('_source', None)
        user_token = request.session.get('_abc_token', None)
        token_introspected_at = request.session.get(
            '_token_introspected_at', None)

        # avoid introspection if it was done last 10 mins
        if token_introspected_at:
            token_introspect_time = make_aware(
                datetime.fromtimestamp(token_introspected_at))
            if now() < token_introspect_time + timedelta(seconds=settings.OAUTH2_INTROSPECT_INTERVAL):
                return None

        request.mi_permission = has_MI_permission
        if source == 'oauth2' and user_token:
            user_access_token = user_token['access_token']
            intro_response = client.post(settings.OAUTH2_INTROSPECT_URL,
                                         data={'token': user_access_token})
            if intro_response.ok:
                response_json = intro_response.json()
                if not response_json['active']:
                    logout(request)
                    raise PermissionDenied()

                self._update_current_user_with_sso_user_id(request, response_json.get('user_id'))
                request.session['_token_introspected_at'] = now().timestamp()
                request.session.save()
                request.mi_permission = True
        return None

    def _update_current_user_with_sso_user_id(self, request, sso_user_id):
        """Check if sso_user_id needs to be updated and update."""
        if not request.user.is_authenticated:
            return

        if sso_user_id is not None and request.user.sso_user_id != sso_user_id:
            request.user.sso_user_id = sso_user_id
            request.user.save()
