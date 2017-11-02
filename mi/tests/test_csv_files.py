from unittest import skip

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from alice.tests.client import AliceClient

from users.models import User


class GenerateOTUForCSV(TestCase):
    def setUp(self):
        self.alice_client = AliceClient()
        self._upload_file()

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
    def _upload_file(self):
        s3_path = 's3://csv.exportwins.dev/export-wins/2017/11/2017-11-01T15:11:42.566651+00:00.csv'
        self._admin_login()
        upload_url = reverse('mi:csv_upload')
        response = self.alice_client.post(
            upload_url, data={'path': s3_path})
        self.assertEqual(response.status_code, 201)

    @skip("Not ready yet")
    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_generate(self):
        self._login()
        latest_url = reverse('mi:csv_latest')
        response = self.alice_client.get(latest_url)
        self.assertEqual(response.status_code, 200)

        file_id = response.data['id']
        generate_url = reverse('mi:csv_generate_otu',
                               kwargs={'file_id': file_id})
        response = self.alice_client.get(generate_url)
        print(response.data['one_time_url'])
        self.assertEqual(response.status_code, 200)
