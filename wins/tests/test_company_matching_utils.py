from django.conf import settings
import requests_mock
from parameterized import parameterized

from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.test import TestCase
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    Timeout,
)
from rest_framework import status

from wins.company_matching_utils import (
    CompanyMatchingServiceConnectionError,
    CompanyMatchingServiceHTTPError,
    CompanyMatchingServiceTimeoutError,
    update_match_ids,
)
from wins.factories import WinFactory
from wins.models import Win
from wins.tests.utils import HawkMockJSONResponse


class TestCompanyMatchingApi(TestCase):
    """
    Tests Company matching API functionality including formating a Company Object
    to JSON to post to the company matching service and error handling.
    """

    @requests_mock.Mocker(kw='requests_mock')
    def test_model_to_match_payload(
        self,
        requests_mock,
    ):
        """
        Test that the function maps the Company object to JSON correctly
        also stripping out falsy values.
        """
        WinFactory(
            id='00000000-0000-0000-0000-000000000000',
            company_name='Name 1',
            cdms_reference='00000000',
            customer_email_address='test@example.com',
        )
        WinFactory(
            id='00000000-0000-0000-0000-000000000001',
            company_name='Name 2',
            cdms_reference='cdms00000000',
            customer_email_address='test@example.com',
        )

        dynamic_response = HawkMockJSONResponse(
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        )
        matcher = requests_mock.post(
            '/api/v1/company/match/',
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )
        update_match_ids(
            Win.objects.filter(customer_email_address='test@example.com')
        )
        assert matcher.called_once
        assert matcher.last_request.json() == {
            'descriptions': [
                {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'company_name': 'Name 1',
                    'contact_email': 'test@example.com',
                    'companies_house_id': '00000000',
                },
                {
                    'id': '00000000-0000-0000-0000-000000000001',
                    'company_name': 'Name 2',
                    'contact_email': 'test@example.com',
                    'cdms_ref': 'cdms00000000',
                },
            ],
        }

    @override_settings(COMPANY_MATCHING_SERVICE_BASE_URL=None)
    def test_missing_settings_error(self):
        """
        Test when environment variables are not set an exception is thrown.
        """
        WinFactory()
        with self.assertRaises(ImproperlyConfigured):
            update_match_ids(Win.objects.all())

    @parameterized.expand(
        [
            (
                ConnectionError,
                CompanyMatchingServiceConnectionError,
            ),
            (
                ConnectTimeout,
                CompanyMatchingServiceConnectionError,
            ),
            (
                Timeout,
                CompanyMatchingServiceTimeoutError,
            ),
            (
                ReadTimeout,
                CompanyMatchingServiceTimeoutError,
            ),
        ],
    )
    @requests_mock.Mocker(kw='requests_mock')
    def test_company_matching_service_request_error(
        self,
        request_exception,
        expected_exception,
        requests_mock,
    ):
        """
        Test if there is an error connecting to company matching service
        the expected exception was thrown.
        """
        requests_mock.post(
            '/api/v1/company/match/',
            exc=request_exception,
        )
        WinFactory()
        with self.assertRaises(expected_exception):
            update_match_ids(Win.objects.all())

    @parameterized.expand(
        [
            (status.HTTP_400_BAD_REQUEST,),
            (status.HTTP_401_UNAUTHORIZED,),
            (status.HTTP_403_FORBIDDEN,),
            (status.HTTP_404_NOT_FOUND,),
            (status.HTTP_405_METHOD_NOT_ALLOWED,),
            (status.HTTP_500_INTERNAL_SERVER_ERROR,),
        ],
    )
    @requests_mock.Mocker(kw='requests_mock')
    def test_company_matching_service_error(
        self,
        response_status,
        requests_mock,
    ):
        """Test if the company matching service returns a status code that is not 200."""
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=response_status,
        )
        WinFactory()
        with self.assertRaises(
            CompanyMatchingServiceHTTPError,
            msg=f'The Company matching service returned an error status: {response_status}',
        ):
            update_match_ids(Win.objects.all())
