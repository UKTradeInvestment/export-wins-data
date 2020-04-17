from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
import pytest
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    Timeout,
)
from rest_framework import status

from wins.factories import WinFactory
from wins.models import Win
from test_helpers.hawk_utils import HawkMockJSONResponse


@pytest.fixture
def create_wins_in_db():
    WinFactory.create(
        id='00000000-0000-0000-0000-000000000000',
        company_name='Name 1',
        cdms_reference='00000000',
        customer_email_address='test@example.com',
    )
    WinFactory.create(
        id='00000000-0000-0000-0000-000000000001',
        company_name='Name 2',
        cdms_reference='cdms00000000',
        customer_email_address='test@example.com',
    )
    WinFactory.create(
        id='00000000-0000-0000-0000-000000000002',
        company_name='Name 2',
        cdms_reference='cdms00000000',
        customer_email_address='test@example.com',
    )


@pytest.fixture
def dynamic_response():
    mock_reponse = {
        'matches': [
            {
                'id': '00000000-0000-0000-0000-000000000000',
                'match_id': 1,
                'similarity': '100000'
            },
            {
                'id': '00000000-0000-0000-0000-000000000001',
                'match_id': 2,
                'similarity': '100000'
            },
            {
                'id': '00000000-0000-0000-0000-000000000002',
                'match_id': None,
                'similarity': '000000'
            },
        ]
    }
    return HawkMockJSONResponse(
        api_id=settings.COMPANY_MATCHING_HAWK_ID,
        api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        response=mock_reponse
    )


@pytest.mark.django_db
class TestUpdateWinMatchIds:
    """Testing import_match_ids Django management command."""

    def test_match_id_update(self, requests_mock, dynamic_response, create_wins_in_db):
        """Test the import_match_ids command updates models succesfully."""
        matcher = requests_mock.post(
            '/api/v1/company/match/',
            text=dynamic_response
        )
        out = StringIO()
        call_command('update_win_match_ids', stdout=out)
        assert matcher.called_once
        assert Win.objects.filter(match_id__isnull=False).count() == 2
        output = out.getvalue()
        assert 'Saved match_id 1 to win:00000000-0000-0000-0000-000000000000' in output
        assert 'Saved match_id 2 to win:00000000-0000-0000-0000-000000000001' in output
        assert '3 Wins successfully updated, completeted' in output

    def test_no_match_given(self, requests_mock, dynamic_response, create_wins_in_db):
        """Test the import_match_ids command updates models succesfully."""
        matcher = requests_mock.post(
            '/api/v1/company/match/',
            text=dynamic_response
        )
        out = StringIO()
        call_command('update_win_match_ids', stdout=out)
        assert matcher.called_once
        assert Win.objects.filter(match_id__isnull=False).count() == 2
        output = out.getvalue()
        assert 'No match found for win:00000000-0000-0000-0000-000000000002 setting to None' in output

    @pytest.mark.parametrize(
        'status_code',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_match_id_update_http_api_error(self, status_code, requests_mock, create_wins_in_db):
        """Test commands raises a Command error on HTTP error status"""
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=status_code
        )
        with pytest.raises(
            CommandError,
            match=rf'Error importing match ids due to an HTTP Error: .+: {status_code}'
        ):
            call_command('update_win_match_ids')

    @pytest.mark.parametrize(
        'exception',
        (
            ConnectionError,
            ConnectTimeout,
            Timeout,
            ReadTimeout,
        ),
    )
    def test_match_id_update_connection_api_error(self, exception, requests_mock, create_wins_in_db):
        """Test commands raises a Command error on client error"""
        requests_mock.post(
            '/api/v1/company/match/',
            exc=exception
        )

        with pytest.raises(
            CommandError,
            match=r'Error importing match ids due to a client error.+',
        ):
            call_command('update_win_match_ids')

    def test_skip_if_win_does_not_exist(self, requests_mock, create_wins_in_db):
        """Test commands skips if the match_id returns a id that is not in the db or not an uuid."""
        mock_reponse = {
            'matches': [
                {
                    'id': 'wrong-id',
                    'match_id': 1,
                    'similarity': '100000'
                },
                {
                    'id': '00000000-0000-0000-0000-000000000099',
                    'match_id': 1,
                    'similarity': '100000'
                },
                {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'match_id': 1,
                    'similarity': '100000'
                },
                {
                    'id': '00000000-0000-0000-0000-000000000001',
                    'match_id': 2,
                    'similarity': '100000'
                },
            ]
        }
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
            response=mock_reponse
        )
        """Test the import_match_ids command updates models succesfully."""
        matcher = requests_mock.post(
            '/api/v1/company/match/',
            text=dynamic_response
        )
        out = StringIO()
        call_command('update_win_match_ids', stdout=out)
        output = out.getvalue()
        assert matcher.called_once
        assert Win.objects.filter(match_id__isnull=False).count() == 2
        assert 'Skipping due to an invalid ID (wrong-id)' in output
        assert 'Skipping due to an invalid ID (00000000-0000-0000-0000-000000000099' in output
