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
import yaml
from django.core.serializers import base
from django.db import DEFAULT_DB_ALIAS, transaction


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
    return _parse_list(value, UUIDField())


def parse_int_list(value):
    """Parses a comma-separated list of Integers from a string."""
    return _parse_list(value, IntegerField())


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


def _parse_list(value, field):
    """Parses a comma-separated list of UUIDs from a string."""
    if not value or value.lower().strip() == 'null':
        return []

    return [field.to_internal_value(item) for item in value.split(',')]


def _build_model_data(model, obj_pk, fields_data, using):
    data = {}
    # Handle each field
    for (field_name, field_value) in fields_data.items():
        field = model._meta.get_field(field_name)

        # Handle many-to-many relations
        if field.many_to_many:
            raise NotImplementedError('Many-to-many fields not supported')

        # Handle one-to-many relations
        if field.one_to_many:
            raise NotImplementedError('One-to-many fields not supported')

        # Handle fk fields
        if field.many_to_one:
            try:
                value = base.deserialize_fk_value(field, field_value, using, False)
            except Exception as exc:
                raise base.DeserializationError.WithData(
                    exc,
                    model._meta.model_name,
                    obj_pk,
                    field_value,
                ) from exc
            data[field.attname] = value
        # Handle all other fields
        else:
            try:
                data[field.name] = field.to_python(field_value)
            except Exception as exc:
                raise base.DeserializationError.WithData(
                    exc,
                    model._meta.model_name,
                    obj_pk,
                    field_value,
                ) from exc
    return data


def _load_data_in_migration(apps, object_list, using=DEFAULT_DB_ALIAS):
    for list_item in object_list:
        obj_pk = list_item.get('pk')
        assert obj_pk, 'pk field required'

        model_label = list_item['model']
        model = apps.get_model(model_label)
        fields_data = list_item['fields']

        model_data = _build_model_data(model, obj_pk, fields_data, using)
        model.objects.update_or_create(pk=obj_pk, defaults=model_data)


@transaction.atomic
def load_yaml_data_in_migration(apps, fixture_file_path):
    """
    Loads the content of the yaml file `fixture_file_path` into the database.
    This is similar to `loaddata` but:
    - it's safe to be used in migrations
    - it does not change the fields that are not present in the yaml

    Motivation:
    Calling `loaddata` from a data migration makes django use the latest version
    of the models instead of the version at the time of that particular migration.
    This causes problems e.g. adding a new field to a model which had a data migration
    in the past is okay but migrating from zero fails as the model in
    loaddata (the latest) has a field that did not exist at that migration time.

    Limitations:
    - Many-to-many fields are not supported yet
    - all items in the yaml have to include a pk field
    """
    with open(fixture_file_path, 'rb') as fixture:
        object_list = yaml.safe_load(fixture)
        _load_data_in_migration(apps, object_list)
