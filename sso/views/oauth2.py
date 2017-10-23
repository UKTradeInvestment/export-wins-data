"""
see http://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#web-application-flow
"""
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from requests_oauthlib import OAuth2Session


def get_oauth_client() -> OAuth2Session:
    return OAuth2Session(
        client_id=settings.OAUTH2_CLIENT_ID,
        redirect_uri=settings.OAUTH2_REDIRECT_URI,
    )


@never_cache
@csrf_exempt
def callback(request):
    """
    frontend will call this and pass through the code from the / o / authorization / url
    """
    oauth = get_oauth_client()
    code = request.POST['code']

    # save token in session? Use token introspection endpoint
    # to check validity periodically? http://localhost:2000/api/v1/user/me/
    token = oauth.fetch_token(token_url=settings.OAUTH2_TOKEN_FETCH_URL, code=code,
                              client_id=settings.OAUTH2_CLIENT_ID, client_secret=settings.OAUTH2_CLIENT_SECRET)

    resp = oauth.get(settings.OAUTH2_USER_PROFILE_URL)
    if resp.ok:
        # figure out who user is and
        abc_data = resp.json()

        user_model = get_user_model()
        # 1. log them in if they already exist
        try:
            user = user_model.objects.get(email=abc_data['email'])
            user.first_name = abc_data['first_name']
            user.last_name = abc_data['last_name']
            user.save()
            login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        # or
        except user_model.models.DoesNotExist:
            # 2. create new User object for them and log them in
            new_user = user_model.objects.create(
                email=abc_data['email'],
                first_name=abc_data['first_name'],
                last_name=abc_data['last_name']
            )
            new_user.set_unusable_password()  # they won't ever need to login using user/pass
            new_user.save()
            login(request, new_user,
                  backend=settings.AUTHENTICATION_BACKENDS[0])
            login(request, new_user)
        return HttpResponse('success')
    else:
        return HttpResponseForbidden()


def auth_url(request):
    """
    returns the url that the frontend should redirect the user to
    """
    url = get_oauth_client().authorization_url(settings.OAUTH2_AUTH_URL)
    return JsonResponse({
        'target_url': url[0],
    })
