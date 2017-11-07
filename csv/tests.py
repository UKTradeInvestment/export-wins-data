from django.test import TestCase, override_settings
from django.urls import reverse

from alice.tests.client import AliceClient

from users.models import User


class CSVUploadPermissionTestCase(TestCase):

    def setUp(self):
        self.alice_client = AliceClient()

    def _login(self, is_staff=False):
        normal_user = User.objects.create_user(
            name='dummy', password="dummy", email='dummy@dummy.com', is_staff=is_staff)
        self.alice_client.force_login(
            normal_user, 'django.contrib.auth.backends.ModelBackend')

    def _admin_login(self):
        admin_user = User.objects.create_superuser(
            name='admin', password="dummy", email='admin@dummy.com')
        self.alice_client.force_login(
            admin_user, 'django.contrib.auth.backends.ModelBackend')

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_csv_upload_allowed_admin_secret(self):
        self._admin_login()
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 201)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_mi_secret(self):
        self._admin_login()
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_ui_secret(self):
        self._admin_login()
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_admin_secret_but_non_staff_normal_user(self):
        self._login()
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_csv_upload_allowed_admin_secret_but_staff_normal_user(self):
        self._login(is_staff=True)
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 201)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_mi_secret_non_staff_normal_user(self):
        self._login()
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_ui_secret_non_staff_normal_user(self):
        self._login()
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_mi_secret_staff_normal_user(self):
        self._login(is_staff=True)
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_ui_secret_staff_normal_user(self):
        self._login(is_staff=True)
        upload_url = reverse("csv:ew_csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)
