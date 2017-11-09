from rest_framework import serializers
from urllib.parse import urlparse
from django.conf import settings

VALID_BUCKET = settings.AWS_BUCKET_CSV


def is_valid_s3_url(value: str):
    parsed_url = urlparse(value)

    # check it's an s3 url
    if not parsed_url.scheme == 's3':
        raise serializers.ValidationError(f'wrong scheme. must be a s3:// url')

    if not parsed_url.netloc.lower() == VALID_BUCKET:
        raise serializers.ValidationError(f'uploaded file must be in the bucket: {VALID_BUCKET}')
