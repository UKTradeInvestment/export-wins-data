import os
import django

from django.conf import settings
from django.core.cache import CacheHandler

from botocore.stub import Stubber


import pytest

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'data.settings_test')


# `pytest` automatically calls this function once when tests are run.
def pytest_configure():
    settings.DEBUG = False
    django.setup()


@pytest.fixture()
def local_memory_cache(monkeypatch):
    """Configure settings.CACHES to use LocMemCache."""
    monkeypatch.setitem(
        settings.CACHES,
        'default',
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    )
    cache_handler = CacheHandler()
    monkeypatch.setattr('django.core.cache.caches', cache_handler)

    yield

    cache_handler['default'].clear()


@pytest.fixture
def api_client():
    """Django REST framework ApiClient instance."""
    from rest_framework.test import APIClient
    yield APIClient()


@pytest.fixture
def s3_stubber():
    from core.utils import get_s3_client_for_bucket

    """S3 stubber using the botocore Stubber class."""
    s3_client = get_s3_client_for_bucket('default')
    with Stubber(s3_client) as s3_stubber:
        yield s3_stubber
