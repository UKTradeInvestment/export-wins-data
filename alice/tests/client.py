from hashlib import sha256

from django.test import Client


class AliceClient(Client):
    """
    Typically, requests need to have a signature added and the Django client
    class doesn't exactly make that easy.
    """

    SIG_KEY = "HTTP_X_SIGNATURE"
    SECRET = "alice_client_test_secret"

    def generic(self, method, path, data='',
                content_type='application/octet-stream', secure=False,
                **extra):

        # This is the only part that isn't copypasta from Client.post
        if self.SIG_KEY not in extra:
            extra[self.SIG_KEY] = self._generate_signature(path, data)

        return Client.generic(
            self,
            method,
            path,
            data=data,
            content_type=content_type,
            secure=secure,
            **extra
        )

    def _generate_signature(self, path, post_data):
        path = bytes(path, "utf-8")
        body = post_data
        secret = bytes(self.SECRET, "utf-8")
        if isinstance(body, str):
            body = bytes(body, "utf-8")

        return sha256(path + body + secret).hexdigest()
