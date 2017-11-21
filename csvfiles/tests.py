import datetime
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings, SimpleTestCase, tag, RequestFactory
from django.urls import reverse
from django.conf import settings

from django.utils.timezone import now
from extended_choices.helpers import ChoiceEntry
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from alice.tests.client import AliceClient
from csvfiles.constants import FILE_TYPES
from csvfiles.serializers import FileTypeChoiceField, MetadataField, FileSerializer
from csvfiles.validators import is_valid_s3_url
from csvfiles.views import CSVBaseView, CSVFileView, PingdomCustomCheckView
from users.factories import UserFactory

from users.models import User


class FileFactory(DjangoModelFactory):

    file_type = FuzzyChoice([x[0] for x in FILE_TYPES])

    class Meta:
        model = 'csvfiles.File'


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


GOOD_FILE_TYPE = 'EXPORT_WINS'
FROZEN_DATE = now()


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


@freeze_time(FROZEN_DATE)
class CSVFileViewTestCase(AuthenticatedRequestFactoryMixin, TestCase):

    def test_immutable_data(self):
        request = self.req()
        view = CSVFileView(file_type=GOOD_FILE_TYPE, request=request)
        self.assertEqual({'user': request.user.id}, view.immutable_data())

    def test_immutable_data_no_user(self):
        request = self.req(user=AnonymousUser())
        view = CSVFileView(file_type=GOOD_FILE_TYPE, request=request)
        self.assertEqual({}, view.immutable_data())

    def test_default_data(self):
        request = self.req()
        view = CSVFileView(file_type=GOOD_FILE_TYPE, request=request)
        self.assertEqual({
            'file_type': FILE_TYPES[GOOD_FILE_TYPE].constant,
            'name': FILE_TYPES[GOOD_FILE_TYPE].display,
            'report_start_date': FROZEN_DATE,
            'report_end_date': FROZEN_DATE
        }, view.default_data())


@tag('csvfiles', 'validation')
class CSVFileValidatorsTestCase(SimpleTestCase):

    @override_settings(AWS_BUCKET_CSV='foo')
    def test_is_valid_s3_url_is_valid(self):
        # will not raise validation error if input is ok
        self.assertEqual(None, is_valid_s3_url("s3://foo/bar"))

    @override_settings(AWS_BUCKET_CSV='foo')
    def test_is_valid_s3_url_is_not_valid(self):
        with self.assertRaises(ValidationError):
            is_valid_s3_url("http://foo/bar")

    @override_settings(AWS_BUCKET_CSV='foo')
    def test_is_valid_s3_url_is_not_valid_mismatch_bucket(self):
        with self.assertRaises(ValidationError) as ve:
            self.assertEqual(None, is_valid_s3_url("s3://bar/foo"))
            ve.msg.contains('bucket')


@tag('csvfiles', 'field')
class CSVFileSerializerFieldTestCase(SimpleTestCase):

    choices = (
        (1, 'test1'),
        (2, 'test2')
    )

    def test_file_type_choice_field(self):
        f = FileTypeChoiceField(self.choices)
        self.assertEqual('test1', f.to_representation(1))

    def test_file_type_choice_field_blank_value(self):
        f = FileTypeChoiceField(self.choices)
        self.assertEqual('', f.to_representation(''))

    def test_file_type_choice_field_null_value(self):
        f = FileTypeChoiceField(self.choices)
        self.assertEqual(None, f.to_representation(None))

    def test_file_type_choice_field_bad_value(self):
        f = FileTypeChoiceField(self.choices)
        with self.assertRaises(KeyError):
            f.to_representation(3)

    def test_metadata_field(self):
        f = MetadataField(metadata_keys=['a', 'b'])
        self.assertEqual({'a': 1, 'b': 2}, f.get_value(
            {'a': 1, 'b': 2, 'c': 3}))

    def test_metadata_field_subset_keys_in_dict(self):
        f = MetadataField(metadata_keys=['a', 'b'])
        self.assertEqual({'b': 2}, f.get_value({'b': 2, 'c': 3}))

    def test_metadata_field_no_subset_keys_in_dict(self):
        f = MetadataField(metadata_keys=['q', 'z'])
        self.assertEqual(None, f.get_value({'b': 2, 'c': 3}))

    def test_metadata_not_required_field(self):
        f = MetadataField(metadata_keys=['q', 'z'], required=False)
        self.assertEqual({}, f.get_value({}))


@tag('csvfiles', 'serializer')
class CSVFileSerializerTestCase(TestCase):

    @override_settings(AWS_BUCKET_CSV='foo')
    def test_fileserializer(self):
        fs = FileSerializer(data={
            'file_type': 'EXPORT_WINS',
            'path': 's3://foo/bar'
        })
        self.assertTrue(fs.is_valid())
        self.assertEqual({}, fs.errors)
        self.assertEqual({
            's3_path': 's3://foo/bar',
            'file_type': 1,
            'metadata': {}
        }, dict(fs.validated_data))


@tag('csvfiles')
@freeze_time(FROZEN_DATE)
class PingdomViewTestCase(TestCase):

    expected_keys = {'status', 'response_time', 'last_uploaded'}

    def assertKeys(self, data):
        self.assertEqual(set(data.keys()), self.expected_keys)

    def test_files_notok_because_none_ever_uploaded(self):
        v = PingdomCustomCheckView()
        data = v.get_context_data()
        self.assertKeys(data)
        self.assertEqual('NOT OK', data['status'])

    def test_files_ok(self):
        for ft_id, ft_const in FILE_TYPES:
            with self.subTest(file_type=ft_id, constant=ft_const):
                f = FileFactory(created=now(), file_type=ft_id)
                v = PingdomCustomCheckView()
                data = v.get_context_data()
                self.assertKeys(data)
                expected_status = 'OK' if ft_id in v._get_filtered_filetypes else 'NOT OK'
                self.assertEqual(expected_status, data['status'], msg=data)
                # it's a subTest so clean up after ourselves
                f.delete()

    def test_files_notok_too_old(self):
        v = PingdomCustomCheckView()
        yesterday_time = now() - datetime.timedelta(seconds=v.error_after_seconds + 1)
        f = FileFactory(file_type=2)
        f.created = yesterday_time
        f.save()
        data = v.get_context_data()
        self.assertKeys(data)
        self.assertEqual('NOT OK', data['status'], msg=data)

    def test_files_notok_wrong_type_uploaded(self):
        v = PingdomCustomCheckView()
        f = FileFactory(file_type=1)
        f.save()
        data = v.get_context_data()
        self.assertKeys(data)
        self.assertEqual('NOT OK', data['status'], msg=data)
