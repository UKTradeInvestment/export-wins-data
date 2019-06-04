from unittest.mock import patch, Mock, MagicMock

from rest_framework import status
from datetime import timedelta, datetime
from django.conf import settings
from django.utils.timezone import now
from freezegun import freeze_time

from django.urls import reverse
from django.test import TestCase, override_settings, tag

from alice.tests.client import AliceClient
from sso.models import AuthorizationState
from users.models import User
from sso.views.oauth2 import callback
from uuid import uuid4

def _mock_check_state(state):
    """Mocked check_state method."""
    return True

def _mock_get_next_url(state):
    """Mocked get_next_url method."""
    return 'https://next'


def _get_user_info(email):
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': email,
    }


def _mock_login(*args, **kwargs):
    """Mocked login method."""
    return True


def _mock_get_oauth_client(user_info):

    def mock_get_oauth_client():
        """Get mocked get_oauth_client."""
        oauth_client = Mock()

        oauth_client.fetch_token.return_value = 'token'

        oauth_get = Mock()
        oauth_get.ok = True
        oauth_get.json.return_value = user_info

        oauth_client.get.return_value = oauth_get

        return oauth_client
    return mock_get_oauth_client


class CallbackViewTestCase(TestCase):
    """Tests for callback view."""

    def _get_request(self):
        """Gets mocked request."""
        request = Mock()
        request.POST = {
            'code': 'code',
            'state': 'state',
        }
        request.session = MagicMock()
        request.session.__setitem__.return_value = None
        request.session.save.return_value = None
        return request

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_creates_new_user_with_sso_user_id(self):
        """Tests that if SSO returns user id then User is created with sso_user_id."""
        user_info = _get_user_info('test@email')
        user_info['user_id'] = str(uuid4())
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user = User.objects.filter(email=user_info['email']).first()
        assert user is not None
        assert user.name == f'{user_info["first_name"]} {user_info["last_name"]}'
        assert str(user.sso_user_id) == user_info['user_id']

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_updates_existing_user_with_sso_user_id(self):
        """Tests that existing user is updated with the sso_user_id."""
        user = User(email='test@email')
        user.save()
        assert user.sso_user_id is None

        user_info = _get_user_info('test@email')
        user_info['user_id'] = str(uuid4())
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user.refresh_from_db()
        assert user.name == f'{user_info["first_name"]} {user_info["last_name"]}'
        assert str(user.sso_user_id) == user_info['user_id']

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_replaces_existing_sso_user_id(self):
        """Tests that existing user's sso_user_id is replaced with new sso_user_id."""
        old_sso_user_id = uuid4()
        user = User(email='test@email', sso_user_id=old_sso_user_id)
        user.save()
        assert user.sso_user_id == old_sso_user_id

        new_sso_user_id = str(uuid4())
        user_info = _get_user_info('test@email')
        user_info['user_id'] = new_sso_user_id
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user.refresh_from_db()
        assert user.name == f'{user_info["first_name"]} {user_info["last_name"]}'
        assert str(user.sso_user_id) == new_sso_user_id


    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_doesnt_update_sso_user_id_if_user_id_not_provided(self):
        """
        Tests that existing user doesn't get sso_user_id updated if not provided
        by auth service.
        """
        user = User(email='test@email')
        user.save()
        assert user.sso_user_id is None

        user_info = _get_user_info('test@email')
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user.refresh_from_db()
        assert user.name == f'{user_info["first_name"]} {user_info["last_name"]}'
        assert user.sso_user_id is None

