from functools import lru_cache

import boto3
import itertools
from collections import defaultdict
from operator import itemgetter
from typing import List, MutableMapping

from django.conf import settings
from rest_framework.fields import (
    BooleanField, CharField, ChoiceField, DateField, DecimalField, EmailField, IntegerField,
    UUIDField,
)

from extended_choices import Choices


def filter_key(dict_, key_to_remove):
    return {k: v for k, v in dict_.items() if k != key_to_remove}


def group_by_key(l: List[MutableMapping], key: str, flatten: bool = False) -> MutableMapping:
    """
    :param l: list of dicts .e.g [{'a': 1, 'b': 1}, {'b': 2, 'a': 2}]
    :param dict_key: the dict key to group by
    :return: a dict with keys and an object or list of objects in the format:
        {1: [{'b': 1}], 2: [{'b': 2}]} or if flatten=True {1: {'b': 1}, 2: {'b': 2}}
    """
    key_getter = itemgetter(key)
    l.sort(key=key_getter)
    groups = defaultdict(list)
    for group, vals in itertools.groupby(l, key=key_getter):
        groups[group] = [filter_key(data, key) for data in vals]
    return {k: v[0] if flatten else v for k, v in groups.items()}


def getitem_or_default(l, idx, default=None):
    """
    gets the item at position idx or returns the default value
    :param list: list of things
    :param idx: position
    :param default: optional default value
    :return: thing at index idx or default
    """
    try:
        return l[idx]
    except IndexError:
        return default


class TrackedSupersetChoices(Choices):
    """
    Same as a normal Choices object except subsets have access to
    their superset.
    """

    def add_subset(self, name, constants):
        super(TrackedSupersetChoices, self).add_subset(name, constants)
        subset = getattr(self, name)
        subset.superset = self


def get_bucket_credentials(bucket_id):
    """Get S3 credentials for bucket id."""
    if bucket_id not in settings.DOCUMENT_BUCKETS:
        raise Exception(f'Bucket "{bucket_id}" not configured.')

    return settings.DOCUMENT_BUCKETS[bucket_id]


def get_bucket_name(bucket_id):
    """Get bucket name for given bucket id."""
    return get_bucket_credentials(bucket_id)['bucket']


@lru_cache()
def get_s3_client_for_bucket(bucket_id):
    """Get S3 client for bucket id."""
    credentials = get_bucket_credentials(bucket_id)
    return boto3.client(
        's3',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        region_name=credentials['aws_region'],
        config=boto3.session.Config(signature_version='s3v4'),
    )


def parse_bool(value):
    """Parses a boolean value from a string."""
    return _parse_value(value, BooleanField())


def parse_date(value):
    """Parses a date from a string."""
    return _parse_value(value, DateField())


def parse_decimal(value, max_digits=19, decimal_places=2):
    """Parses a decimal from a string."""
    return _parse_value(value, DecimalField(max_digits, decimal_places))


def parse_email(value):
    """Parses an email address from a string."""
    return _parse_value(value, EmailField(), blank_value='')


def parse_uuid(value):
    """Parses a UUID from a string."""
    return _parse_value(value, UUIDField())


def parse_int(value):
    """Parses a integer from a string."""
    return _parse_value(value, IntegerField())


def parse_uuid_list(value):
    """Parses a comma-separated list of UUIDs from a string."""
    if not value or value.lower().strip() == 'null':
        return []

    field = UUIDField()

    return [field.to_internal_value(item) for item in value.split(',')]


def parse_choice(value, choices, blank_value=''):
    """Parses and validates a value from a list of choices."""
    return _parse_value(value, ChoiceField(choices=choices), blank_value=blank_value)


def parse_limited_string(value, max_length=settings.CHAR_FIELD_MAX_LENGTH):
    """Parses/validates a string."""
    return _parse_value(value, CharField(max_length=max_length), blank_value='')


def _parse_value(value, field, blank_value=None):
    if not value or value.lower().strip() == 'null':
        return blank_value

    field.run_validation(value)
    return field.to_internal_value(value)
