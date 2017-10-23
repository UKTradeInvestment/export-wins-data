from django.conf.urls import url

from sso.views import (
    auth_url,
    callback,
)

urlpatterns = [
    url(r'^callback/$', callback, name="oauth2_callback"),
    url(r'^auth_url/$', callback, name="oauth2_auth_url")
]
