import datetime

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient

from test_helpers.mock_views import HawkViewWithScope
from test_helpers.hawk_utils import hawk_auth_sender as _hawk_auth_sender
from users.factories import UserFactory


def _url():
    return 'http://testserver' + reverse('hawk-view-without-scope')


def _url_incorrect_domain():
    return 'http://incorrect' + reverse('hawk-view-without-scope')


def _url_incorrect_path():
    return 'http://testserver' + reverse('hawk-view-without-scope') + 'incorrect/'


def _url_with_scope():
    return 'http://testserver' + reverse('hawk-view-with-scope')


def resolve_data(params):
    return {
        key: value() if callable(value) else value for (key, value) in params.items()
    }


def hawk_auth_sender(url, **kwargs):
    """Pass credentials to hawk sender."""
    extra = {
        'key_id': 'no-scope-id',
        'secret_key': 'no-scope-key',
        **kwargs
    }
    return _hawk_auth_sender(url, **extra)


@pytest.fixture
def api_client():
    yield APIClient()


@pytest.mark.django_db
@pytest.mark.urls('core.tests.urls')
class TestHawkAuthentication:
    """Tests Hawk authentication when using HawkAuthentication."""

    @pytest.mark.parametrize(
        'get_kwargs,expected_json',
        (
            (
                # If the Authorization header isn't passed
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Authentication credentials were not provided.'},
            ), (
                # If the Authorization header generated from an incorrect ID
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url(), key_id='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect secret
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(
                        _url(),
                        secret_key='incorrect'
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect domain
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url_incorrect_domain()).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect path
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url_incorrect_path()).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from incorrect content
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url(), content='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_invalid_key_401_returned(self, api_client, get_kwargs, expected_json):
        """If the request isn't properly Hawk-authenticated, then a 401 is
        returned
        """
        response = api_client.get(
            _url(),
            **resolve_data(get_kwargs),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    @pytest.mark.parametrize(
        'get_kwargs,expected_json',
        (
            (
                # If no X-Forwarded-For header
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url()).request_header,
                }, {
                    'detail': 'Incorrect authentication credentials.'
                },
            ), (
                # If second-to-last X-Forwarded-For header isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url()).request_header,
                    'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For is whitelisted
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url()).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url()).request_header,
                    'HTTP_X_FORWARDED_FOR': '123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If third-to-last IP in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url()).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If last of 3 IPs in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': lambda: hawk_auth_sender(_url()).request_header,
                    'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_wrong_ip_forward_401_returned(self, api_client, get_kwargs, expected_json):
        """If the request isn't properly Hawk-authenticated, then a 401 is
        returned
        """
        response = api_client.get(
            _url(),
            **resolve_data(get_kwargs),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    def test_if_61_seconds_in_past_401_returned(self, api_client):
        """If the Authorization header is generated 61 seconds in the past, then a
        401 is returned
        """
        past = datetime.datetime.now() - datetime.timedelta(seconds=61)
        with freeze_time(past):
            auth = hawk_auth_sender(_url()).request_header
        response = api_client.get(
            _url(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Incorrect authentication credentials.'}

    @pytest.mark.usefixtures('local_memory_cache')
    def test_if_authentication_reused_401_returned(self, api_client):
        """If the Authorization header is reused, then a 401 is returned"""
        auth = hawk_auth_sender(_url()).request_header

        response_1 = api_client.get(
            _url(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response_1.status_code == status.HTTP_200_OK

        response_2 = api_client.get(
            _url(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response_2.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_2.json() == {'detail': 'Incorrect authentication credentials.'}

    def test_empty_object_returned_with_authentication_3_ips(self, api_client):
        """If the Authorization and X-Forwarded-For headers are correct,
        with an extra IP address prepended to the X-Forwarded-For then
        the correct, and authentic, data is returned
        """
        auth = hawk_auth_sender(_url()).request_header
        response = api_client.get(
            _url(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'content': 'hawk-test-view-without-scope'}


@pytest.mark.django_db
@pytest.mark.urls('core.tests.urls')
class TestHawkResponseSigning:
    """Tests Hawk response signing when using HawkResponseMiddleware."""

    def test_empty_object_returned_with_authentication(self, api_client):
        """If the Authorization and X-Forwarded-For headers are correct, then
        the correct, and authentic, data is returned
        """
        sender = hawk_auth_sender(_url())
        response = api_client.get(
            _url(),
            content_type='',
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )

        assert response.has_header('server-authorization')
        sender.accept_response(
            response.get('Server-Authorization'),
            content=response.content,
            content_type=response.get('Content-Type'),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_does_not_sign_non_hawk_requests(self):
        """Test that a 403 is returned if the request is not authenticated using Hawk."""
        from rest_framework.test import force_authenticate

        factory = APIRequestFactory()
        user = UserFactory.create()

        view = HawkViewWithScope.as_view()

        request = factory.get('/hawk-view-without-scope/')
        force_authenticate(request, user=user)
        response = view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }


@pytest.mark.django_db
@pytest.mark.urls('core.tests.urls')
class TestHawkScopePermission:
    """Tests scoped-based permissions using HawkScopePermission."""

    def test_denies_access_when_without_the_required_scope(self, api_client):
        """
        Test that a 403 is returned if the request is Hawk authenticated but the client doesn't
        have the required scope.
        """
        auth = hawk_auth_sender(
            _url_with_scope(),
            key_id='no-scope-id',
            secret_key='no-scope-key',
        ).request_header
        response = api_client.get(
            _url_with_scope(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'You do not have permission to perform this action.',
        }

    def test_denies_access_if_not_authenticated_using_hawk(self):
        """Test that a 403 is returned if the request is not authenticated using Hawk."""
        from rest_framework.test import force_authenticate

        factory = APIRequestFactory()
        user = UserFactory.create()
        view = HawkViewWithScope.as_view()

        request = factory.get('/hawk-view-without-scope/')
        force_authenticate(request, user=user)
        response = view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            'detail': 'You do not have permission to perform this action.',
        }

    def test_authorises_when_with_the_required_scope(self, api_client):
        """
        Test that a 200 is returned if the request is Hawk authenticated and the client has
        the required scope.
        """
        auth = hawk_auth_sender(
            _url_with_scope(),
            key_id='single-scope-id',
            secret_key='single-scope-key',
        ).request_header
        response = api_client.get(
            _url_with_scope(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'content': 'hawk-test-view-with-scope'}

    def test_authorises_when_with_one_of_the_required_scopes(self, api_client):
        """
        Test that a 200 is returned if the request is Hawk authenticated and the client has
        one of the required scope.
        """
        auth = hawk_auth_sender(
            _url_with_scope(),
            key_id='mulit-scope-id',
            secret_key='mulit-scope-key',
        ).request_header
        response = api_client.get(
            _url_with_scope(),
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'content': 'hawk-test-view-with-scope'}
