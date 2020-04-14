import mohawk


def hawk_auth_sender(url, key_id='some-id', secret_key='some-secret', method='GET',
                     content='', content_type=''):
    credentials = {
        'id': key_id,
        'key': secret_key,
        'algorithm': 'sha256',
    }
    return mohawk.Sender(
        credentials,
        url,
        method,
        content=content,
        content_type=content_type,
    )
