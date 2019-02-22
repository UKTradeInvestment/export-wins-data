from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from rest_framework import status

from sso.models import ADFSUser
from test_helpers.base import AliceAPIRequestFactory
from users.views import LoggedInUserRetrieveViewSet


class UserViewsTestCase(TestCase):

    url = reverse('user_profile')
    factory = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_login_time = now()
        cls.user = ADFSUser.objects.create(
            email='test@exmaple.com',
            last_login=cls.user_login_time,
        )
        cls.factory = AliceAPIRequestFactory(user=cls.user)

    @property
    def view(self):
        return LoggedInUserRetrieveViewSet.as_view({'get': 'retrieve'})

    def test_adfs_user_returns_valid_result(self):
        req = self.factory.get(self.url)
        resp = self.view(req)
        self.assertEqual(resp.data['email'], self.user.get_username())
        self.assertEqual(parse_datetime(resp.data['last_login']), self.user_login_time)
        self.assertEqual(resp.data['permitted_applications'], {})

    def test_return_permitted_applications_from_session(self):
        req = self.factory.get(self.url)
        session = req.session
        session['_abc_permitted_applications'] = {'key': 'athena'}
        session.save()

        resp = self.view(req)

        self.assertEqual(resp.data['permitted_applications'], {'key': 'athena'})

    def test_response_has_max_age(self):
        req = self.factory.get(self.url)
        resp = self.view(req)
        self.assertIn('cache-control', resp._headers.keys())
        _, cache_control = resp._headers['cache-control']
        self.assertRegex(cache_control, r'^max-age=.*$')

    @override_settings(API_DEBUG=True)
    def test_anonymous_user_returns_dummy_user(self):
        """
        This should only happen if API_DEBUG is Flas, but this tests
        that even in that scenario we define sensible behaviour
        """
        anon_factory = AliceAPIRequestFactory()
        req = anon_factory.get(self.url)
        resp = self.view(req)
        self.assertIn('cache-control', resp._headers.keys())
        _, cache_control = resp._headers['cache-control']
        self.assertRegex(cache_control, r'^max-age=.*$')
        self.assertEqual(resp.data['email'], 'api_debug@true')
        self.assertEqual(resp.data['last_login'], None)

    @override_settings(API_DEBUG=False)
    def test_anonymous_user_returns_403(self):
        """
        This should only happen if API_DEBUG is Flas, but this tests
        that even in that scenario we define sensible behaviour
        """
        anon_factory = AliceAPIRequestFactory()
        req = anon_factory.get(self.url)
        resp = self.view(req)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
