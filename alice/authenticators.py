from django.conf import settings

from rest_framework.permissions import BasePermission, SAFE_METHODS


class AlicePermission(BasePermission):
    """
    Allows a GET request to schema, and view-defined requests to everything
    else so long as they're authenticated.
    """

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            if hasattr(view, 'action') and view.action == "schema":
                return True

        # as IsAuthenticated permission
        if request.user and request.user.is_authenticated():
            return True

        return False


class IsServer(BasePermission):
    """ Abstract class to check if request is from expected server


    Child classes just need to inherit and specify `server_name` attribute
    """

    def has_permission(self, request, view):
        if settings.DEBUG and settings.API_DEBUG:
            return True
        return request.server_name == self.server_name


class IsAdminServer(IsServer):
    server_name = 'admin'


class IsMIServer(IsServer):
    server_name = 'mi'


class IsMIUser(BasePermission):
    """
    Allows access only to MI users.
    """

    def is_member(self, user):
        return user.groups.filter(name='mi_group').exists()

    def has_permission(self, request, view):
        if settings.DEBUG and settings.API_DEBUG:
            return True
        return request.user and request.user.is_authenticated() and self.is_member(request.user)
