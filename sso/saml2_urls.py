from django.conf.urls import url

from djangosaml2.views import metadata

from sso.views.saml import (
    assertion_consumer_service,
    login,
    logout,
    ADFSAttributesView,
)

urlpatterns = [
    url(r'^metadata/$', metadata, name='saml2_metadata'),
    url(r'^login/$', login, name='saml2_login'),
    url(r'^acs/$', assertion_consumer_service, name='saml2_acs'),
    url(r'^attributes/$', ADFSAttributesView.as_view(), name='adfs_attributes'),
    url(r'^logout/$', logout, name='adfs_logout'),
    # url(r'^ls/$', logout_service, name='saml2_ls'),
    # url(r'^ls/post/$', logout_service_post, name='saml2_ls_post'),
]
