import json

from django.conf import settings
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import parsers, renderers, mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.authenticators import IsMIServer, IsMIUser
from .serializers import LoggingAuthTokenSerializer, UserSerializer


class LoginView(APIView):

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (
        parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = LoggingAuthTokenSerializer
    http_method_names = ("post")

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # get authenticated user (will raise exception otherwise)
        user = serializer.validated_data['user']

        # create session for the user
        login(request, user)

        return Response({
            'id': user.pk,
            'email': user.email,
            'is_staff': user.is_staff,
        })


class LogoutView(APIView):

    renderer_classes = (renderers.JSONRenderer,)

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        auth_logout(request)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Logout may be done via POST."""
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return Response({})


class IsLoggedIn(APIView):
    permission_classes = (AllowAny,)
    http_method_names = ("get",)

    def get(self, request):
        return HttpResponse(json.dumps(bool(request.user.is_authenticated)))


class UserRetrieveViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsMIServer, IsMIUser)
    serializer_class = UserSerializer
    http_method_names = ('get')

    def get_object(self):
        u = self.request.user
        if isinstance(u, AnonymousUser):
            if settings.API_DEBUG:
                u.email = 'api_debug@true'
                u.last_login = None
            elif hasattr(self.request, 'adfs_attributes'):
                u.email = self.request.adfs_attributes['emailaddress'][0]
            else:
                raise PermissionDenied()
        return u

    def get_queryset(self):
        return []

    def retrieve(self, request, *args, **kwargs):
        resp = super().retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'max-age={}'.format(request.session.get_expiry_age())
        return resp
