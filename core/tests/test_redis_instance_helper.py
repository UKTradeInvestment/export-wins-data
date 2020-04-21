import json

import pytest
from django.core.exceptions import ImproperlyConfigured

from data.settings import get_redis_instance


@pytest.fixture
def vcap_service(monkeypatch):
    VCAP_SERVICES = {
        'redis': [
            {
                'credentials': {
                    'uri': 'redis://redis-1'
                },
                'name': 'redis-1',
            },
            {
                'credentials': {
                    'uri': 'redis://redis-2'
                },
                'name': 'redis-2',
            },
        ]
    }
    monkeypatch.setenv('VCAP_SERVICES', json.dumps(VCAP_SERVICES))


class TestRedisInstanceHelper:
    """Switch redis instance base on environment variable."""

    def test_credentials_are_returned(self, monkeypatch, vcap_service):
        """Test instance is returned when the name is matched."""
        monkeypatch.setenv("REDIS_SERVICE_NAME", "redis-2")
        credentials = get_redis_instance()
        assert credentials.get('uri') == 'redis://redis-2'

    def test_missing_env_raises_error(self, monkeypatch, vcap_service):
        """Test missing env raises error."""
        monkeypatch.delenv("REDIS_SERVICE_NAME")

        with pytest.raises(ImproperlyConfigured):
            get_redis_instance()

    def test_return_first_instance_when_there_is_one(self, monkeypatch):
        """Test if only one instance is available return the frist one."""
        VCAP_SERVICES = {
            'redis': [
                {
                    'credentials': {
                        'uri': 'redis://redis-1'
                    },
                    'name': 'redis-1',
                },
            ]
        }
        monkeypatch.setenv('VCAP_SERVICES', json.dumps(VCAP_SERVICES))
        monkeypatch.setenv("REDIS_SERVICE_NAME", "redis-2")
        credentials = get_redis_instance()
        assert credentials.get('uri') == 'redis://redis-1'
