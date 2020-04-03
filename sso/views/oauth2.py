"""
This is oauth2 implementation for DIT Authentication Broker Component
that centralises SSO for all DIT applications
This is not a typical oauth2 implementation, in order to keep saml2 as backup authentication
for web-application-flow
see http://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html
"""
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from requests_oauthlib import OAuth2Session

from sso.models import AuthorizationState


def get_oauth_client(redirect_uri=settings.OAUTH2_REDIRECT_URI) -> OAuth2Session:
    return OAuth2Session(
        client_id=settings.OAUTH2_CLIENT_ID, redirect_uri=redirect_uri,
    )


@never_cache
@csrf_exempt
def callback(request):
    """
    frontend will call this and pass through the code from the ABC callback url
    if the user exists in database, we log them in
    otherwise we create a new user and log them in,
    thus assuming any user authenticated by ABC is a valid MI user
    Returns a JSON with front end's follow up URL, if any
    """

    code = request.POST['code']
    state = request.POST.get('state', '')[:254]

    if not AuthorizationState.objects.check_state(state):
        return HttpResponseBadRequest('bad state')

    redirect_uri = request.POST.get("redirect_uri", settings.OAUTH2_REDIRECT_URI)

    oauth = get_oauth_client(redirect_uri=redirect_uri)

    token = oauth.fetch_token(
        token_url=settings.OAUTH2_TOKEN_FETCH_URL,
        code=code,
        client_id=settings.OAUTH2_CLIENT_ID,
        client_secret=settings.OAUTH2_CLIENT_SECRET,
    )

    # to check validity periodically, refresh_token?
    # obtain user profile /api/v1/user/me/
    resp = oauth.get(settings.OAUTH2_USER_PROFILE_URL)
    if resp.ok:
        # figure out who user is and
        abc_data = resp.json()

        permitted_applications = abc_data.get('permitted_applications', {})

        user = _get_or_create_user(abc_data)

        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

        request.session['_source'] = 'oauth2'
        request.session['_abc_token'] = token
        request.session['_abc_permitted_applications'] = permitted_applications
        request.session['_token_introspected_at'] = now().timestamp()

        request.session.save()

        json_response = {
            'next': AuthorizationState.objects.get_next_url(state),
            'user': {'id': user.id, 'email': user.email, 'is_staff': user.is_staff},            
        }

        return JsonResponse(json_response)
    else:
        return HttpResponseForbidden()


def auth_url(request):
    """
    returns the url that the frontend should redirect the user to
    save the state for future cross check in callback
    save and pass follow up url to the front end via callback
    """

    redirect_uri = request.GET.get("redirect_uri", settings.OAUTH2_REDIRECT_URI)

    url, state = get_oauth_client(redirect_uri).authorization_url(settings.OAUTH2_AUTH_URL)
    next_url = request.GET.get('next', None)
    AuthorizationState.objects.create(state=state, next_url=next_url)
    return JsonResponse({'target_url': url})


@transaction.atomic
def _get_or_create_user(abc_data):
    """
    This logic is necessarily complex as there is a shared user list for MI (which uses SSO for
    authentication) and Export Wins (which does not use SSO for authentication).

    The following scenarios need to be handled:

    1. New user (not previously seen by either email or SSO user ID)
    2. Existing Export Wins-only user (match of existing user by email only)
    3a. Existing MI user but not Export Wins (match of existing user by SSO user ID only,
    has unusable password)
    3b. Existing MI and Export Wins user (match of existing user by SSO user ID only, has usable
    password)
    4. Two different existing Export Wins and MI users (two different matches by email and by SSO
    user ID)

    In the fourth case, the SSO user ID is transferred to the user with the matching email
    address to avoid altering their Export Wins data.
    """
    user_model = get_user_model()

    user_for_email = user_model.objects.filter(
        email__iexact=abc_data['email'],
    ).first()

    user_for_sso_user_id = user_model.objects.filter(
        sso_user_id=abc_data['user_id'],
    ).first()

    # Scenarios 2 and 4
    if user_for_email and user_for_sso_user_id != user_for_email:
        if user_for_sso_user_id:
            user_for_sso_user_id.sso_user_id = None
            user_for_sso_user_id.save()

        _update_user(user_for_email, abc_data)
        return user_for_email

    # Scenarios 3a and 3b
    if user_for_sso_user_id:
        _update_user(user_for_sso_user_id, abc_data)
        return user_for_sso_user_id

    # Scenario 1
    return _create_user(abc_data)


def _update_user(user, abc_data):
    # For scenario 3b
    # Don't update the email address if the user has a valid Export Wins login (partly as there
    # is no guarantee that the new email address is the one they use for receiving email)
    if not user.has_usable_password():
        user.email = abc_data['email']

    user.name = _format_name(abc_data)
    user.sso_user_id = abc_data['user_id']
    user.save()


def _create_user(abc_data):
    user_model = get_user_model()

    new_user = user_model.objects.create(
        email=abc_data['email'],
        name=_format_name(abc_data),
        sso_user_id=abc_data['user_id'],
    )

    # As this is an MI-only user, they won't need to login using a password
    new_user.set_unusable_password()
    new_user.save()
    return new_user


def _format_name(abc_data):
    name_parts = (abc_data['first_name'], abc_data['last_name'])
    name = ' '.join(filter(None, name_parts))
    return name.strip()[:128]
