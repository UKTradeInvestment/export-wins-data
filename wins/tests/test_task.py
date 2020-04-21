from unittest.mock import patch, Mock

import pytest

from celery.exceptions import Retry
from django.conf import settings
from django.db.models.signals import post_save
from factory.django import mute_signals
from requests.exceptions import ConnectTimeout, ReadTimeout
from rest_framework.status import HTTP_200_OK

from wins.company_matching_utils import CompanyMatchingServiceException
from wins.factories import WinFactory
from wins.tasks.match_id_task import update_match_id
from test_helpers.hawk_utils import HawkMockJSONResponse


@pytest.mark.django_db
class TestMatchIdTask:
    """Test task to update match id."""

    @mute_signals(post_save)
    def test_update_match_id_task(self, requests_mock):
        """Test task updates match id."""
        win = WinFactory(
            id='00000000-0000-0000-0000-000000000001',
            company_name='Name 2',
            cdms_reference='cdms00000000',
            customer_email_address='test@example.com',
        )

        mock_reponse = {
            'matches': [
                {
                    'id': '00000000-0000-0000-0000-000000000001',
                    'match_id': 1,
                    'similarity': '100000'
                },
            ]
        }

        dynamic_response = HawkMockJSONResponse(
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
            response=mock_reponse,
        )
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=HTTP_200_OK,
            text=dynamic_response,
        )
        update_match_id.delay(win.pk)
        win.refresh_from_db()
        assert win.match_id == 1

    @mute_signals(post_save)
    @pytest.mark.parametrize(
        'exception',
        (
            ConnectTimeout,
            ReadTimeout,
        ),
    )
    def test_error_retry(self, requests_mock, exception, monkeypatch):
        """Test task updates match id."""
        win = WinFactory(
            id='00000000-0000-0000-0000-000000000001',
            company_name='Name 2',
            cdms_reference='cdms00000000',
            customer_email_address='test@example.com',
        )

        requests_mock.post(
            '/api/v1/company/match/',
            exc=exception,
        )

        retry_mock = Mock(side_effect=Retry(exc=CompanyMatchingServiceException()))
        monkeypatch.setattr(update_match_id, 'retry', retry_mock)

        with pytest.raises(Retry):
            update_match_id(win.pk)

        assert retry_mock.call_count == 1
