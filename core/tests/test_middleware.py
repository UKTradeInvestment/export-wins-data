from unittest.mock import patch, Mock
from uuid import uuid4

from django.test import TestCase

from core.middleware import RequestLoggerMiddleware
from users.models import User


def _mock_get_response(request):
    response = Mock()
    response.status_code = 200
    return response


class RequestLoggerMiddlewareTestCase(TestCase):
    """Tests for RequestLoggerMiddleware."""

    def setUp(self):
        self.middleware = RequestLoggerMiddleware(get_response=_mock_get_response)
        self.user = User(email='what@email.com', sso_user_id=uuid4())

    def _create_request(self):
        request = Mock()
        request.method = 'GET'
        request.user = None
        request.get_full_path.return_value = '/somepath'
        return request

    def _create_logged_in_request(self):
        request = self._create_request()
        request.user = self.user
        return request

    def _create_logged_in_request_no_sso_user_id(self):
        request = self._create_request()
        request.user = User(email='another@email', sso_user_id=None)
        return request

    @patch('core.middleware.logger.info')
    def test_request_with_sso_user_id_is_logged(self, info):
        """Tests that sso_user_id is included in the request log."""
        request = self._create_logged_in_request()
        self.middleware(request)

        info.assert_called_with('request', extra={
            'method': 'GET',
            'path': '/somepath',
            'status_code': 200,
            'local_user_id': self.user.id,
            'sso_user_id': self.user.sso_user_id,
        })

    @patch('core.middleware.logger.info')
    def test_request_without_user_is_logged(self, info):
        """Tests that request without user is logged."""
        request = self._create_request()
        self.middleware(request)

        info.assert_called_with('request', extra={
            'method': 'GET',
            'path': '/somepath',
            'status_code': 200,
            'local_user_id': None,
            'sso_user_id': None,
        })

    @patch('core.middleware.logger.info')
    def test_request_without_sso_user_id_is_logged(self, info):
        """Tests that local_user_id is included in the request log."""
        request = self._create_logged_in_request_no_sso_user_id()
        self.middleware(request)

        info.assert_called_with('request', extra={
            'method': 'GET',
            'path': '/somepath',
            'status_code': 200,
            'sso_user_id': None,
            'local_user_id': request.user.id,
        })
