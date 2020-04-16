from unittest.mock import patch, Mock, MagicMock

import pytest
from rest_framework import status

from django.test import TestCase

from users.models import User
from sso.views.oauth2 import callback
from uuid import uuid4


def _mock_check_state(_):
    """Mocked check_state method."""
    return True


def _mock_get_next_url(_):
    """Mocked get_next_url method."""
    return 'https://next'


def _get_user_info(email, sso_user_id):
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': email,
        'user_id': sso_user_id,
    }


def _mock_login(*args, **kwargs):
    """Mocked login method."""
    return True


def _mock_get_oauth_client(user_info):
    def mock_get_oauth_client(redirect_uri):
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

    def validate_oauth_response(self, actual_response, user):
        expected_content = f'{{"next": "https://next", "user": {{"id": {user.id}, "email": "{user.email}", "is_staff": false}}}}'
        expected_response = bytearray(expected_content, 'utf-8')
        assert expected_response == actual_response

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_when_user_exists_with_sso_match(self):
        existing_user = User(email='existing_sso_user@export.wins', sso_user_id=uuid4())
        existing_user.save()

        user_info = _get_user_info('sso_email_address@export.wins', existing_user.sso_user_id)
        user_info['contact_email'] = 'sso_contact_email_address@export.wins'
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK

        existing_user.refresh_from_db()
        assert existing_user.email == user_info['contact_email']

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_when_user_exists_with_sso_match_and_contact_email_collision(self):
        contact_email = 'sso_contact_email@export.wins'

        existing_user = User(email='existing_sso_user@export.wins', sso_user_id=uuid4())
        existing_user.save()
        collision_user = User(email=contact_email)
        collision_user.save()

        user_info = _get_user_info('sso_email_address@export.wins', existing_user.sso_user_id)
        user_info['contact_email'] = contact_email

        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        existing_user.refresh_from_db()
        assert existing_user.email == contact_email

        collision_user.refresh_from_db()
        assert collision_user.email != contact_email
        assert collision_user.email == "_" + contact_email

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_when_user_matches_on_sso_email(self):
        sso_email = 'sso_email@export.wins'
        new_contact_email = 'updated_contact_email@export.wins'

        existing_user = User(email=sso_email)
        existing_user.save()

        user_info = _get_user_info(sso_email, uuid4())
        user_info['contact_email'] = new_contact_email
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        existing_user.refresh_from_db()
        assert existing_user.sso_user_id == user_info['user_id']
        assert existing_user.email == new_contact_email

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_when_user_matches_on_sso_email_and_collision_on_contact_email(self):
        sso_email = 'sso_email@export.wins'
        new_contact_email = 'updated_contact_email@export.wins'

        existing_user = User(email=sso_email)
        existing_user.save()

        collision_user = User(email=new_contact_email)
        collision_user.save()

        user_info = _get_user_info(sso_email, uuid4())
        user_info['contact_email'] = new_contact_email
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        existing_user.refresh_from_db()
        assert existing_user.sso_user_id == user_info['user_id']
        assert existing_user.email == new_contact_email

        collision_user.refresh_from_db()
        assert collision_user.email != new_contact_email
        assert collision_user.sso_user_id is None
        assert collision_user.email == "_" + new_contact_email

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_when_user_matches_on_contact_email(self):
        contact_email = 'contact_email@export.wins'
        sso_email = 'no_match@export.wins'

        existing_user = User(email=contact_email)
        existing_user.save()

        user_info = _get_user_info(sso_email, uuid4())
        user_info['contact_email'] = contact_email
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        existing_user.refresh_from_db()
        assert existing_user.sso_user_id == user_info['user_id']
        assert existing_user.email == contact_email
