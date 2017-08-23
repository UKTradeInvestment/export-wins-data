from hashlib import sha256

from django.test import Client
from requests.auth import AuthBase

SIG_KEY = "HTTP_X_SIGNATURE"


def _generate_signature(secret, path, post_data):
    path = bytes(path, "utf-8")
    body = post_data
    secret = bytes(secret, "utf-8")
    if isinstance(body, str):
        body = bytes(body, "utf-8")

    return sha256(path + body + secret).hexdigest()


class AliceClient(Client):
    """
    Typically, requests need to have a signature added and the Django client
    class doesn't exactly make that easy.
    """

    SECRET = "alice_client_test_secret"

    def generic(self, method, path, data='',
                content_type='application/octet-stream', secure=False,
                **extra):

        # This is the only part that isn't copypasta from Client.post
        if SIG_KEY not in extra:
            extra[SIG_KEY] = self.sign(path, data)

        return Client.generic(
            self,
            method,
            path,
            data=data,
            content_type=content_type,
            secure=secure,
            **extra
        )

    def sign(self, path, post_data):
        return _generate_signature(self.SECRET, path, post_data)


class AliceAuthenticator(AuthBase):
    """
    Alice authenticator that can be used with `requests`.
    >>> from alice.tests.client import AliceAuthenticator
    >>> import requests
    >>> requests.get('http://localhost:8000/some_path/', auth=AliceAuthenticator('SECRET!!!'))
    <Response [200]>
    """

    def __init__(self, secret, header=SIG_KEY):
        super().__init__()
        self.secret = secret
        self.header = header

    def __call__(self, r):
        sig = _generate_signature(self.secret, r.url, r.body or '')
        r.headers[self.header] = sig
        return r
