from unittest.mock import patch
from xml.etree import ElementTree

from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from alice.tests.client import AliceClient
from sso.models import ADFSUser


class BaseSSOTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice_client = AliceClient()
        cls.adfs_user = ADFSUser(email='test@example.com')
        cls.adfs_user.save()

    def _login(self):
        # note login side-steps SAML/XML stuff
        self.alice_client.force_login(self.adfs_user)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    @patch('sso.middleware.get_user_attributes', lambda _: {})
    def _get_status(self, url, status_code=200, perm=False):
        if perm:
            with patch('sso.middleware.has_MI_permission', lambda _: True):
                response = self.alice_client.get(url)
        else:
            response = self.alice_client.get(url)
        self.assertEqual(response.status_code, status_code)
        return response

    def _get(self, name, status_code=200, perm=False):
        url = reverse('sso:' + name)
        return self._get_status(url, status_code, perm)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def _post(self, name, post_dict, status_code=200):
        response = self.alice_client.post(reverse(name), post_dict)
        self.assertEqual(response.status_code, status_code)
        return response


class SSOTestCase(BaseSSOTestCase):

    def _assert_response_has_strings(self, response, expected_strs):
        content = response.content.decode("utf-8")
        for expected_str in expected_strs:
            self.assertTrue(expected_str in content)

    def test_metadata(self):
        response = self._get('saml2_metadata')
        ElementTree.fromstring(response.content)  # check well formed
        expected = [
            'AuthnRequestsSigned="true"',
            'WantAssertionsSigned="true"',
            'entityID="https://sso.datahub.service.trade.gov.uk/sp"',
            'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
        ]
        self._assert_response_has_strings(response, expected)

    def test_login(self):
        response = self._get('saml2_login')
        expected = [
            'document.SSO_Login.submit()',
            'name="SAMLRequest"',
            '<input type="submit" value="Log in" />',
        ]
        self._assert_response_has_strings(response, expected)
        self.assertGreater(len(response.content), 2000)

    def test_acs_not_post(self):
        self._get('saml2_acs', 400)

    def test_acs_bad_post(self):
        self._post('sso:saml2_acs', {}, 400)

    # def test_acs_valid(self):
    #     self._post('saml2_acs', {'SAMLResponse': '<xml>'})
    #     # mock everything?

    def _assert_not_logged_in_adfs(self):
        self._get('adfs_attributes', 403)

    def test_adfs_not_logged_in_rejected(self):
        self._assert_not_logged_in_adfs()

    def test_adfs_access_no_perm(self):
        self._login()
        self._get('adfs_attributes', 403)

    def test_adfs_access_with_perm(self):
        self._login()
        self._get('adfs_attributes', perm=True)

    def test_logout(self):
        self._login()
        self._get('adfs_logout')
        self._assert_not_logged_in_adfs()
