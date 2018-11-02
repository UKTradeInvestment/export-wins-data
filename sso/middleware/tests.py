from unittest.mock import patch, Mock, MagicMock
from uuid import uuid4

from django.test import TestCase

from sso.middleware.oauth2 import OAuth2IntrospectToken
from users.models import User


def _get_user_info(email, active=True):
    return {
        'active': active,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': email,
    }


def _mock_oauth2_session(user_info):
    """Fake Oauth2Session object to let us test OAuth2IntrospectToken."""
    def mock_oauth2_session(**kwargs):
        session = Mock()

        intro_response = Mock()
        intro_response.ok = True
        intro_response.json.return_value = user_info

        session.post.return_value = intro_response

        return session
    return mock_oauth2_session


def _fake_session(key, default=None):
    """Returns fake session data."""
    if key == '_source':
        return 'oauth2'
    if key == '_abc_token':
        return {
            'access_token': 'token',
        }
    return default


class OAuth2IntrospectTokenMiddlewareTestCase(TestCase):
    """Tests for callback view."""

    def _create_request(self):
        """Gets mocked request."""
        request = Mock()
        request.POST = {
            'code': 'code',
            'state': 'state',
        }
        request.user = User(email='test@email')
        request.user.save()
        request.session = MagicMock()
        request.session.__setitem__.return_value = None
        request.session.__getitem__.side_effect = _fake_session
        request.session.get.side_effect = _fake_session
        request.session.save.return_value = None
        return request

    @patch('sso.middleware.oauth2.has_MI_permission', True)
    @patch('sso.middleware.oauth2.OAuth2Session', _mock_oauth2_session)
    def test_middleware_updates_sso_user_id(self):
        """Tests that if SSO returns user id then User is created with sso_user_id."""
        user_info = _get_user_info('test@email')
        user_info['user_id'] = str(uuid4())

        mock_oauth2_session = _mock_oauth2_session(user_info)

        request = self._create_request()

        middleware = OAuth2IntrospectToken()

        with patch('sso.middleware.oauth2.OAuth2Session', mock_oauth2_session):
            middleware.process_request(request)

        user = User.objects.filter(email=user_info['email']).first()
        assert str(user.sso_user_id) == user_info['user_id']

    @patch('sso.middleware.oauth2.has_MI_permission', True)
    @patch('sso.middleware.oauth2.OAuth2Session', _mock_oauth2_session)
    def test_middleware_updates_sso_user_id(self):
        """Tests that if SSO returns user id then User is created with sso_user_id."""
        user_info = _get_user_info('test@email')

        mock_oauth2_session = _mock_oauth2_session(user_info)

        request = self._create_request()

        middleware = OAuth2IntrospectToken()

        with patch('sso.middleware.oauth2.OAuth2Session', mock_oauth2_session):
            middleware.process_request(request)

        user = User.objects.filter(email=user_info['email']).first()
        assert user.sso_user_id is None
