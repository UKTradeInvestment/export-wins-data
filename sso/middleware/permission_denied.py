from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from django.conf import settings


class Metadata403(MiddlewareMixin):

    def process_response(self, request, response):
        if getattr(response, 'status_code', None) == status.HTTP_403_FORBIDDEN:
            response['PreferAuthWith'] = settings.SSO_PREFER_AUTH
        return response
