from unittest.mock import patch

from datetime import timedelta, datetime
from django.conf import settings
from django.utils.timezone import now
from freezegun import freeze_time

from django.urls import reverse
from django.test import TestCase, override_settings, tag

from alice.tests.client import AliceClient
from sso.models import AuthorizationState
from users.models import User


class BaseSSOTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice_client = AliceClient()
        cls.adfs_user = User(email='test@example.com')
        cls.adfs_user.save()

    def _login(self):
        self.alice_client.force_login(
            self.adfs_user, 'django.contrib.auth.backends.ModelBackend')

    def _get_status_no_secret(self, url, status_code=200, perm=False):
        if perm:
            with patch('sso.middleware.saml2.has_MI_permission', lambda _: True):
                response = self.alice_client.get(url)
        else:
            response = self.alice_client.get(url)
        self.assertEqual(response.status_code, status_code)
        return response

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def _get_status_admin_secret(self, *args, **kwargs):
        return self._get_status_no_secret(*args, **kwargs)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def _get_status_mi_secret(self, *args, **kwargs):
        return self._get_status_no_secret(*args, **kwargs)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _get_status_ui_secret(self, *args, **kwargs):
        return self._get_status_no_secret(*args, **kwargs)

    def _get(self, name, status_code=200, perm=False):
        url = reverse('oauth2:' + name)
        return self._get_status_mi_secret(url, status_code, perm)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def _post(self, name, post_dict, status_code=200):
        response = self.alice_client.post(reverse(name), post_dict)
        self.assertEqual(response.status_code, status_code)
        return response

    def _get_api_response(self, url, status_code=200):
        self._login()
        return self._get_status_mi_secret(url, status_code=status_code, perm=True)


# mi secret tests?

class SSOTestCase(BaseSSOTestCase):

    def _assert_response_has_strings(self, response, expected_strs):
        content = response.content.decode("utf-8")
        for expected_str in expected_strs:
            self.assertTrue(expected_str in content)

@tag('oauth2')
@freeze_time(datetime(2017, 1, 1, 12))
@override_settings(OAUTH2_STATE_TIMEOUT_SECONDS=1)
class AuthorizationStateTestCase(TestCase):

    def _create_state(self, state):
        return AuthorizationState.objects.create(state=state)

    def _make_invalid(self, authState: AuthorizationState):
        timeout = settings.OAUTH2_STATE_TIMEOUT_SECONDS
        authState.created = now() - timedelta(seconds=timeout + 1)
        authState.save()
        return AuthorizationState.objects.get(state=authState.state)

    def test_no_states_in_valid_qs(self):
        # create 1 invalid state
        self._make_invalid(self._create_state('123'))
        self.assertEqual(AuthorizationState.objects.all().count(), 1)
        self.assertEqual(AuthorizationState.objects.valid().count(), 0)

    def test_1_valid_state_is_in_valid_qs(self):
        self._create_state('222')
        self.assertEqual(AuthorizationState.objects.all().count(), 1)
        self.assertEqual(AuthorizationState.objects.valid().count(), 1)

    def test_1_valid_1_invalid_in_qs(self):
        self._make_invalid(self._create_state('123'))
        self._create_state('222')
        self.assertEqual(AuthorizationState.objects.all().count(), 2)
        self.assertEqual(AuthorizationState.objects.valid().count(), 1)

    def test_check_state_for_valid_state(self):
        self._create_state('333')
        self.assertEqual(AuthorizationState.objects.valid().count(), 1)
        self.assertTrue(AuthorizationState.objects.check_state('333'))

    def test_check_state_for_expired_state(self):
        self._make_invalid(self._create_state('444'))
        self.assertEqual(AuthorizationState.objects.all().count(), 1)
        self.assertEqual(AuthorizationState.objects.valid().count(), 0)
        self.assertFalse(AuthorizationState.objects.check_state('444'))

    def test_check_state_deletes_expired_ones(self):
        self._make_invalid(self._create_state('444'))
        self.assertEqual(AuthorizationState.objects.all().count(), 1)
        self.assertEqual(AuthorizationState.objects.valid().count(), 0)
        self.assertFalse(AuthorizationState.objects.check_state('444'))
        self.assertEqual(AuthorizationState.objects.all().count(), 0)
