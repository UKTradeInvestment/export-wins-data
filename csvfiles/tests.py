from django.test import TestCase, override_settings, SimpleTestCase, tag, RequestFactory
from django.urls import reverse
from django.conf import settings

from extended_choices.helpers import ChoiceEntry

from alice.tests.client import AliceClient
from csvfiles.views import CSVBaseView, CSVFileView
from users.factories import UserFactory

from users.models import User


class CSVUploadPermissionTestCase(TestCase):

    VALID_BUCKET = settings.AWS_BUCKET_CSV
    VALID_S3_PATH = 's3://{}/export-wins/2017/11/2017-11-01T15:11:42.566651+00:00.csv'.format(
        VALID_BUCKET)

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
            upload_url, data={'path': self.VALID_S3_PATH})
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
            upload_url, data={'path': self.VALID_S3_PATH})
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

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_ew_csv_list(self):
        self._login()
        url = reverse("csv:ew_csv_list")
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, 200)


GOOD_FILE_TYPE = 'EXPORT_WINS'


@tag('csvfiles', 'views')
class CSVFileBaseViewTestCase(SimpleTestCase):

    def test_bad_filetype(self):
        with self.assertRaises(ValueError):
            CSVBaseView.as_view(file_type='foo')

        f = CSVBaseView.as_view(file_type=GOOD_FILE_TYPE)
        self.assertEqual(f.view_initkwargs['file_type'], GOOD_FILE_TYPE)

    def test_filetype_kwarg_resolves_to_correct_choices_object(self):
        view = CSVBaseView(file_type=GOOD_FILE_TYPE)
        self.assertIsInstance(view.file_type_choice, ChoiceEntry)
        self.assertEqual(view.file_type_choice.constant, GOOD_FILE_TYPE)


class AuthenticatedRequestFactoryMixin():

    factory = RequestFactory()

    def req(self, path='/', user=None):
        request = self.factory.get(path)
        request.user = user or UserFactory()
        return request


@tag('csvfiles', 'views')
class CSVFileViewTestCase(AuthenticatedRequestFactoryMixin, TestCase):

    def test_immutable_data(self):
        request = self.req()
        view = CSVFileView(file_type=GOOD_FILE_TYPE, request=request)
        self.assertEqual({'user': request.user.id}, view.immutable_data())
