import datetime

import mohawk
import pytest
from django.conf import settings
from django.core.cache import CacheHandler
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from test_helpers.hawk_utils import hawk_auth_sender as _hawk_auth_sender


def hawk_auth_sender(url, **kwargs):
    """Pass credentials to hawk sender."""
    extra = {
        'key_id': 'activity-stream-id',
        'secret_key': 'activity-stream-key',
        **kwargs
    }
    return _hawk_auth_sender(url, **extra)


def multi_scope_hawk_auth_sender(url, **kwargs):
    """Pass multi scope hawk id is for backwards compatibilty."""
    extra = {
        'key_id': 'mulit-scope-id',
        'secret_key': 'mulit-scope-key',
        **kwargs
    }
    return _hawk_auth_sender(url, **extra)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def local_memory_cache(monkeypatch):
    monkeypatch.setitem(
        settings.CACHES,
        'default',
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    )
    monkeypatch.setattr('django.core.cache.caches', CacheHandler())


def _url():
    return 'http://testserver' + reverse('activity-stream')


def _url_incorrect_domain():
    return 'http://incorrect' + reverse('activity-stream')


def _url_incorrect_path():
    return 'http://testserver' + reverse('activity-stream') + 'incorrect/'


@pytest.mark.parametrize(
    'get_kwargs,expected_json',
    (
        (
            # If no X-Forwarded-For header
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(_url()).request_header,
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If second-to-last X-Forwarded-For header isn't whitelisted
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(_url()).request_header,
                HTTP_X_FORWARDED_FOR='9.9.9.9, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the only IP address in X-Forwarded-For is whitelisted
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(_url()).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the only IP address in X-Forwarded-For isn't whitelisted
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(_url()).request_header,
                HTTP_X_FORWARDED_FOR='123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If third-to-last IP in X-Forwarded-For header is whitelisted
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(_url()).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 124.124.124, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If last of 3 IPs in X-Forwarded-For header is whitelisted
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(_url()).request_header,
                HTTP_X_FORWARDED_FOR='124.124.124, 123.123.123.123, 1.2.3.4',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header isn't passed
            dict(
                content_type='',
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Authentication credentials were not provided.'},
        ),
        (
            # If the Authorization header generated from an incorrect ID
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url(),
                    key_id='incorrect',
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect secret
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url(),
                    secret_key='incorrect'
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect domain
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url_incorrect_domain(),
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect path
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url_incorrect_path(),
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect method
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url(),
                    method='POST',
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from an incorrect
            # content-type
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url(),
                    content_type='incorrect',
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
        (
            # If the Authorization header generated from incorrect content
            dict(
                content_type='',
                HTTP_AUTHORIZATION=hawk_auth_sender(
                    _url(),
                    content='incorrect',
                ).request_header,
                HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
            ),
            {'detail': 'Incorrect authentication credentials.'},
        ),
    ),
)
@pytest.mark.django_db
def test_401_returned(api_client, get_kwargs, expected_json):
    """If the request isn't properly Hawk-authenticated, then a 401 is
    returned
    """
    response = api_client.get(
        _url(),
        **get_kwargs,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == expected_json


@pytest.mark.django_db
@pytest.mark.parametrize(
    'hawk_auth_sender',
    (
        multi_scope_hawk_auth_sender,
        hawk_auth_sender
    )
)
def test_if_61_seconds_in_past_401_returned(api_client, hawk_auth_sender):
    """If the Authorization header is generated 61 seconds in the past, then a
    401 is returned
    """
    past = datetime.datetime.now() - datetime.timedelta(seconds=61)
    with freeze_time(past):
        auth = hawk_auth_sender(_url()).request_header
    response = api_client.get(
        reverse('activity-stream'),
        content_type='',
        HTTP_AUTHORIZATION=auth,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = {'detail': 'Incorrect authentication credentials.'}
    assert response.json() == error


@pytest.mark.usefixtures('local_memory_cache')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'hawk_auth_sender',
    (
        multi_scope_hawk_auth_sender,
        hawk_auth_sender
    )
)
def test_if_authentication_reused_401_returned(api_client, hawk_auth_sender):
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
    error = {'detail': 'Incorrect authentication credentials.'}
    assert response_2.json() == error


@pytest.mark.django_db
@pytest.mark.parametrize(
    'hawk_auth_sender',
    (
        multi_scope_hawk_auth_sender,
        hawk_auth_sender
    )
)
def test_empty_object_returned_with_authentication_3_ips(api_client, hawk_auth_sender):
    """If the Authorization and X-Forwarded-For headers are correct,
    with an extra IP address prepended to the X-Forwarded-For then
    the correct, and authentic, data is returned
    """
    sender = hawk_auth_sender(_url())
    response = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )

    assert response.status_code == status.HTTP_200_OK
    content = {'secret': 'content-for-pen-test'}
    assert response.json() == content


@pytest.mark.django_db
@pytest.mark.parametrize(
    'hawk_auth_sender',
    (
        multi_scope_hawk_auth_sender,
        hawk_auth_sender
    )
)
def test_empty_object_returned_with_authentication(api_client, hawk_auth_sender):
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

    assert response.status_code == status.HTTP_200_OK
    content = {'secret': 'content-for-pen-test'}
    assert response.json() == content

    # Just asserting that accept_response doesn't raise is a bit weak,
    # so we also assert that it raises if the header, content, or
    # content_type are incorrect
    sender.accept_response(
        response_header=response['Server-Authorization'],
        content=response.content,
        content_type=response['Content-Type'],
    )
    with pytest.raises(mohawk.exc.MacMismatch):
        sender.accept_response(
            response_header=response['Server-Authorization'] + 'incorrect',
            content=response.content,
            content_type=response['Content-Type'],
        )
    with pytest.raises(mohawk.exc.MisComputedContentHash):
        sender.accept_response(
            response_header=response['Server-Authorization'],
            content='incorrect',
            content_type=response['Content-Type'],
        )
    with pytest.raises(mohawk.exc.MisComputedContentHash):
        sender.accept_response(
            response_header=response['Server-Authorization'],
            content=response.content,
            content_type='incorrect',
        )


@pytest.mark.django_db
def test_no_scope(api_client):
    """
    Test request returns a 403 if keys are out of scope
    """
    auth_header = hawk_auth_sender(
        _url(),
        key_id='no-scope-id',
        secret_key='no-scope-key'
    ).request_header

    response = api_client.get(
        _url(),
        content_type='',
        HTTP_AUTHORIZATION=auth_header,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
