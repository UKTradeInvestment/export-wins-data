from unittest.mock import patch, Mock, MagicMock

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

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_creates_new_user_with_sso_user_id(self):
        """
        Tests that if SSO returns user id then User is created with sso_user_id.

        (Scenario 1.)
        """
        user_info = _get_user_info('test@email', str(uuid4()))
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
    def test_callback_replaces_existing_sso_user_id_if_email_matches(self):
        """
        Tests that an existing user with a matching email address has its sso_user_id updated.

        (Scenario 2.)
        """
        user = User(email='test@email')
        user.save()
        assert user.sso_user_id is None

        user_info = _get_user_info('test@email', str(uuid4()))
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
    def test_callback_updates_existing_user_if_sso_user_id_matches(self):
        """
        Tests that an existing user with an unusable password and a matching SSO user ID has has
        other details updated.

        (Scenario 3a.)
        """
        sso_user_id = str(uuid4())
        user = User(email='old@email', sso_user_id=sso_user_id)
        user.set_unusable_password()
        user.save()

        user_info = _get_user_info('new@email', sso_user_id)
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user.refresh_from_db()
        assert user.name == f'{user_info["first_name"]} {user_info["last_name"]}'
        assert user.email == 'new@email'

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_does_not_update_email_if_has_usable_password(self):
        """
        Tests that an existing user with a usable password and a matching SSO user ID does
        not have its email address updated.

        (Scenario 3b.)
        """
        sso_user_id = str(uuid4())
        user = User(email='old@email', sso_user_id=sso_user_id)
        user.set_password('test-password')
        user.save()

        user_info = _get_user_info('new@email', sso_user_id)
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user.refresh_from_db()
        assert user.name == f'{user_info["first_name"]} {user_info["last_name"]}'
        assert user.email == 'old@email'

    @patch('sso.views.oauth2.AuthorizationState.objects.check_state', _mock_check_state)
    @patch('sso.views.oauth2.AuthorizationState.objects.get_next_url', _mock_get_next_url)
    @patch('sso.views.oauth2.login', _mock_login)
    def test_callback_transfers_sso_user_id_if_conflicting_existing_users(self):
        """
        Test that if there are both existing users for the sso_user_id and email address,
        the sso_user_id is transferred to the correct user.

        (Scenario 4.)
        """
        existing_sso_user_id = str(uuid4())
        existing_email = 'test@email'

        user_with_matching_sso_user_id = User(
            email='other@email',
            sso_user_id=existing_sso_user_id,
        )
        user_with_matching_sso_user_id.save()

        user_with_matching_email = User(
            email=existing_email,
            sso_user_id=str(uuid4()),
        )
        user_with_matching_email.save()

        user_info = _get_user_info(existing_email, existing_sso_user_id)
        mock_oauth_client = _mock_get_oauth_client(user_info)

        request = self._get_request()

        with patch('sso.views.oauth2.get_oauth_client', mock_oauth_client):
            response = callback(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'{"next": "https://next"}'

        user_with_matching_sso_user_id.refresh_from_db()
        assert user_with_matching_sso_user_id.sso_user_id is None

        user_with_matching_email.refresh_from_db()
        assert str(user_with_matching_email.sso_user_id) == existing_sso_user_id
        assert user_with_matching_email.name == (
            f'{user_info["first_name"]} {user_info["last_name"]}'
        )
