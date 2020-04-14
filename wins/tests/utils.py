from datetime import datetime

from rest_framework.fields import DateField, DateTimeField


def format_date_or_datetime(value):
    """
    Formats a date or datetime using DRF fields.

    This is for use in tests when comparing dates and datetimes with JSON-formatted values.
    """
    if isinstance(value, datetime):
        return DateTimeField().to_representation(value)
    return DateField().to_representation(value)