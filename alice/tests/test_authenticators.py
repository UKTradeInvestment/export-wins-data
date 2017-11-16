from unittest import mock

from django.test import TestCase, Client, override_settings, RequestFactory, SimpleTestCase
from django.core.urlresolvers import reverse

from ..authenticators import AlicePermission
from ..middleware import SignatureRejectionMiddleware, alice_exempt
from .client import AliceClient


class BaseSignatureTestCase(SimpleTestCase):
    """
    Base TestCase providing a mock request and appropriate signature
    """

    def setUp(self):
        self.request = RequestFactory().get('/path')
        self.request._body = b'lol'
        # signature generated from alice test client and above path & body
        self.sig = (
            '32e92ae0b2815281bfcda9b4f1c08babe4386fffca7109987c911189402a5dfd'
        )


class SignatureRejectionMiddlewareTestCase(BaseSignatureTestCase):

    def setUp(self):
        super().setUp()
        self.middleware = SignatureRejectionMiddleware()

    def test_generate_signature(self):
        signature = self.middleware._generate_signature(
            'secret',
            'path',
            b'body',
        )
        self.assertEqual(
            signature,
            'c6be1984f8b516e94d7257031cc47ed9863a433e461ac0117214b1b6a7801991',
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_test_signature_missing(self):
        self.assertFalse(self.middleware._test_signature(self.request))

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_test_signature_incorrect(self):
        self.request.META['HTTP_X_SIGNATURE'] = 'bad-signature'
        self.assertFalse(self.middleware._test_signature(self.request))

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_test_signature_correct(self):
        self.request.META['HTTP_X_SIGNATURE'] = self.sig
        self.assertTrue(self.middleware._test_signature(self.request))

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_process_request_pass(self):
        self.request.META['HTTP_X_SIGNATURE'] = self.sig
        self.assertEqual(self.middleware.process_view(self.request, lambda: True, (), {}), None)

    def test_process_request_fail(self):
        response = self.middleware.process_view(self.request, lambda: True, (), {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'PFO')

    def test_process_request_not_fail_if_exempt(self):
        response = self.middleware.process_view(self.request, alice_exempt(lambda: True), (), {})
        self.assertEqual(response, None)


class AlicePermissionTestCase(BaseSignatureTestCase):

    def setUp(self):
        super().setUp()
        self.view = mock.Mock()
        self.request.user = mock.Mock()
        self.request.user.is_authenticated = lambda: False
        self.alice_perm = AlicePermission().has_permission

    def test_has_permission_schema_valid_signature(self):
        self.view.action = 'schema'
        self.assertTrue(self.alice_perm(self.request, self.view))

    def test_has_permission_nonschema_invalid_signature(self):
        self.assertFalse(self.alice_perm(self.request, self.view))

    def test_has_permission_nonschema_not_authenticated(self):
        self.assertFalse(self.alice_perm(self.request, self.view))

    def test_has_permission_nonschema_authenticated(self):
        self.request.user.is_authenticated = lambda: True
        self.assertTrue(self.alice_perm(self.request, self.view))
