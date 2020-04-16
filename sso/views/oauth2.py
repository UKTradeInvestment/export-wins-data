"""
This is oauth2 implementation for DIT Authentication Broker Component
that centralises SSO for all DIT applications
This is not a typical oauth2 implementation, in order to keep saml2 as backup authentication
for web-application-flow
see http://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html
"""
import logging
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from requests_oauthlib import OAuth2Session

from sso.models import AuthorizationState

logger = logging.getLogger(__name__)


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
    Login is only via SSO
    1. Matching SSO user_id - just update the user's email
    2. Match on SSO email - update the user.sso_user_id to user_id and update the email
    3. Match on SSO contact_email - update the user.sso_user_id and email
    4. Create a new user

    """
    user_model = get_user_model()

    user = user_model.objects.filter(
        sso_user_id=abc_data['user_id'],
    ).first()

    # 1 a straight match on SSO - update that user details and archive any others
    if user:
        logger.debug(f"user {user.id} match on sso_user_id")
        return _safe_update_user(user, abc_data)

    user_matched_by_email = user_model.objects.filter(
        email=abc_data['email']
    ).first()

    # 2 there was no SSO match try to find a email only login and update it
    if user_matched_by_email:
        logger.debug(f"user {user_matched_by_email.id} match on SSO email")
        return _safe_update_user(user_matched_by_email, abc_data)

    # 3 no SSO match try to match against the SSO contact_email address
    if 'contact_email' in abc_data:
        user_matched_by_contact_email = user_model.objects.filter(
            email=abc_data['contact_email']
        ).first()

        # is there an edge case here if abc_data['contact_email'] is blank???
        if user_matched_by_contact_email:
            logger.debug(f"user {user_matched_by_contact_email.id} match on SSO contact_email")
            return _safe_update_user(user_matched_by_contact_email, abc_data)

    # 4 Brand new user
    logger.debug(f"create user {abc_data['email']}")
    return _create_user(abc_data)


def _archive_existing_user_by_email(email, sso_id):
    # we want to update the email address for a user
    # so we need to check for collisions i.e. if the email address is associated with a different user
    # if this happens we just prefix the username and deactivate it
    user_model = get_user_model()

    existing_user = user_model.objects.filter(
        email=email,
    ).first()

    # No collisions - do nothing
    if not existing_user:
        return

    # this is the same user!
    if sso_id and existing_user.sso_user_id == sso_id:
        return

    existing_user.email = "_" + existing_user.email
    existing_user.is_active = False

    existing_user.save()


def _get_contact_email_fallback_to_email(abc_data):
    # We default to SSO email field unless there is a value for contact_email
    # (email is mandatory in SSO)
    if 'contact_email' in abc_data:
        return abc_data['contact_email']

    return abc_data['email']


def _safe_update_user(user, abc_data):
    email = _get_contact_email_fallback_to_email(abc_data)

    if user.email == email and user.sso_user_id == abc_data['user_id']:
        return user

    _archive_existing_user_by_email(email, user.sso_user_id)

    user.email = email
    user.name = _format_name(abc_data)
    user.sso_user_id = abc_data['user_id']
    user.save()
    return user


def _create_user(abc_data):
    user_model = get_user_model()

    email = _get_contact_email_fallback_to_email(abc_data)

    new_user = user_model.objects.create(
        email=email,
        name=_format_name(abc_data),
        sso_user_id=abc_data['user_id'],
    )

    new_user.save()
    return new_user


def _format_name(abc_data):
    name_parts = (abc_data['first_name'], abc_data['last_name'])
    name = ' '.join(filter(None, name_parts))
    return name.strip()[:128]
