import json
import logging

import saml2
from saml2.client import Saml2Client
from saml2.ident import code, decode

import django
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
)
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import djangosaml2
from djangosaml2.backends import Saml2Backend
from djangosaml2.cache import (
    IdentityCache,
    OutstandingQueriesCache,
    StateCache,
)
from djangosaml2.conf import get_config
from rest_framework.views import APIView

from mi.views.base_view import MI_PERMISSION_CLASSES

logger = logging.getLogger(__name__)

"""

This file is our own handling for SSO & users, a mixture of custom code,
djangosaml2 and django auth. This is done for the following reasons:

- to avoid polluting/breaking the existing fragile Export Wins code e.g.
  having to change AUTHENTICATION_BACKENDS
- to reasonably cleanly handle the necessary hacking around AUTH_USER_MODEL
- to improve the djangosaml2 code to be more understandable/hackable e.g.
  to add sha256 support
- to use djangosaml2 just as purely backend talking to a seperate front end,
  instead of as a complete Django app as designed
- this can be fairly simply unwound into using the regular user model when the
  app gets split out
- ...

See also SSOMiddleware

"""


def login(request):
    """ Stripped & simplified version of djangosaml2.views.login

    Generates some HTML for front end to return to user, which contains
    Javascript which POSTs appropriate Base64 encoded XML generated by
    pysaml2 & xmlsec for Core ADFS IdP.

    Also added support for SHA256 signing.

    """
    conf = get_config()
    client = Saml2Client(conf)
    came_from = '/'
    session_id, result = client.prepare_for_authenticate(
        entityid=None,
        relay_state=came_from,
        binding=saml2.BINDING_HTTP_POST,
        sign_alg=saml2.xmldsig.SIG_RSA_SHA256,
    )
    oq_cache = OutstandingQueriesCache(request.session)
    oq_cache.set(session_id, came_from)

    params = djangosaml2.utils.get_hidden_form_inputs(result['data'][3])
    response = render(
        request,
        'djangosaml2/example_post_binding_form.html',
        {
            'target_url': result['url'],
            'params': params,
        },
    )
    return response


def has_MI_permission(adfs_attributes):
    if settings.SAML_DONT_CHECK_GROUP_MEMBERSHIP:
        return True
    return 'AG-DataHub-MI' in adfs_attributes.get('group', [])


@csrf_exempt
def assertion_consumer_service(request):
    """ Stripped & simplified version of equivalent from djangosaml2.views

    SAML Authorization Response endpoint

    The front end will pass over IdP response to this endpoint for processing
    by pysaml2 and authentication with djangosaml2 backend.

    """
    if not request.POST.get('SAMLResponse'):
        return HttpResponseBadRequest('No SAMLResponse')

    xmlstr = request.POST['SAMLResponse']
    conf = get_config()
    client = Saml2Client(conf, identity_cache=IdentityCache(request.session))
    oq_cache = OutstandingQueriesCache(request.session)
    outstanding_queries = oq_cache.outstanding_queries()
    response = client.parse_authn_request_response(
        xmlstr,
        saml2.BINDING_HTTP_POST,
        outstanding_queries,
    )
    session_id = response.session_id()
    oq_cache.delete(session_id)

    # authenticate the remote user
    session_info = response.session_info()
    djangosaml2_backend = Saml2Backend()
    attribute_mapping = {'uid': ('username', )}  # unnecessary but required
    user = djangosaml2_backend.authenticate(
        session_info=session_info,
        create_unknown_user=True,
        attribute_mapping=attribute_mapping,
    )
    if not user:
        return HttpResponseBadRequest('Couldn\'t get user')

    user.backend = 'djangosaml2.backends.Saml2Backend'
    django.contrib.auth.login(request, user)
    request.session['_saml2_subject_id'] = code(session_info['name_id'])

    adfs_attributes = get_user_attributes(request)
    if not has_MI_permission(adfs_attributes):
        err = {'code': 1, 'message': 'user does not have MI permission'}
        resp = HttpResponseForbidden(json.dumps(err))
        resp['Content-Type'] = 'application/json'
        err['identity'] = adfs_attributes
        logger.error(err)
        return resp

    return HttpResponse('success')


def get_user_attributes(request):
    """ For authenticated user, get ADFS attributes from session cache

    Based on djangosaml2.views.echo_attributes

    """
    state = StateCache(request.session)
    conf = get_config()
    identity_cache = IdentityCache(request.session)
    client = Saml2Client(
        conf,
        state_cache=state,
        identity_cache=identity_cache,
    )
    subject_id = _get_subject_id(request.session)
    identity = client.users.get_identity(subject_id)
    return identity[0]


class ADFSAttributesView(APIView):
    permission_classes = MI_PERMISSION_CLASSES

    def get(self, request):
        return HttpResponse(request.adfs_attributes.items())


# this gives Core error at the moment, todo
# def logout(request):
#     """ Stripped & simplified version of djangosaml2.views.logout

#     Uses pysaml2 to create LogoutRequest. Added SHA256.

#     """
#     if not authenticated(request):
#         return HttpResponseBadRequest('not logged in')

#     state = StateCache(request.session)
#     conf = get_config()
#     client = Saml2Client(
#         conf,
#         state_cache=state,
#         identity_cache=IdentityCache(request.session),
#     )
#     subject_id = _get_subject_id(request.session)
#     result = client.global_logout(
#         subject_id,
#         # sign_alg=saml2.xmldsig.SIG_RSA_SHA256,
#     )
#     state.sync()
#     if not result:
#         return HttpResponseBadRequest("You are not logged in any IdP/AA")

#     assert len(result) == 1

#     entityid, logout_info = result.popitem()
#     assert isinstance(logout_info, tuple)
#     binding, http_info = logout_info
#     assert binding == saml2.BINDING_HTTP_POST
#     body = ''.join(http_info['data'])
#     print('returning form to user to POST to IdP', body)
#     return HttpResponse(body)


def _get_subject_id(session):
    try:
        return decode(session['_saml2_subject_id'])
    except KeyError:
        return None


def logout(request):
    """ Logout from Django only, not ADFS """

    request.session.flush()
    return HttpResponse('success')
