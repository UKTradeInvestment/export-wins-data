from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now
from importlib import import_module
from rest_framework.test import APIRequestFactory, force_authenticate

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class AliceAPIRequestFactory(APIRequestFactory):
    """
    A RequestFactory you can use to access views protected by Alice.
    This is nice because it's faster than using the alice_client but the
    downside is that no middleware is executed.

    It also allows you to specify a user to authenticate as
    """

    user = None

    def __init__(self, user=None):
        self.user = user
        super().__init__()

    def generic(self, method, path, data='',
                content_type='application/octet-stream', secure=False,
                **extra):
        req = super().generic(method, path, data=data, content_type=content_type, **extra)
        if self.user:
            force_authenticate(req, user=self.user)
        req.server_name = 'mi'
        req.mi_permission = True
        s = SessionStore()
        s.expire_date=now() + timedelta(days=1)
        s.create()
        req.session = s
        return req
