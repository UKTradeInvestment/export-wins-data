import pytest
from django.urls import reverse
from rest_framework import status

from fixturedb.factories.win import create_win_factory
from wins.constants import BUSINESS_POTENTIAL
from wins.factories import BreakdownFactory, CustomerResponseFactory, HVCFactory, UserFactory, WinFactory
from wins.tests.utils import format_date_or_datetime
from test_helpers.hawk_utils import hawk_auth_sender as _hawk_auth_sender


@pytest.fixture
def hvc_win():
    """Set up datbase records for testing hvc win in data hub."""
    hvc = HVCFactory.create(
        campaign_id='E083',
        name='E083 - Consumer Goods & Retail',
        financial_year=16,
    )
    win = create_win_factory(UserFactory.create())(
        hvc_code='E083',
        sector_id=88,
        confirm=True,
    )
    BreakdownFactory.create(year=2020, win=win)
    BreakdownFactory.create(year=2021, win=win)
    return hvc, win


@pytest.fixture
def non_hvc_win():
    """Set up datbase records for testing non_hvc win in data hub."""
    win = create_win_factory(UserFactory.create())(
        hvc_code=None,
        sector_id=88,
        confirm=True,
    )
    BreakdownFactory.create(year=2020, win=win)
    BreakdownFactory.create(year=2021, win=win)
    return win


def _url(match_id):
    path = reverse('wins-by-match-id', kwargs={'match_id': match_id})
    return 'http://testserver' + path


def hawk_auth_sender(url, **kwargs):
    """Pass credentials to hawk sender."""
    extra = {
        'key_id': 'data-hub-id',
        'secret_key': 'data-hub-key',
        **kwargs,
    }
    return _hawk_auth_sender(url, **extra)


@pytest.mark.django_db
class TestWinDataHubView:
    """Test exports wins endpoint for data hub"""

    @pytest.mark.parametrize('verb', ('post', 'patch', 'delete'))
    def test_verbs_not_allowed(self, api_client, verb):
        """Test only get is supported"""
        url = _url(3)
        auth = hawk_auth_sender(url, method=verb).request_header
        response = getattr(api_client, verb)(
            url,
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_wrong_scope(self, api_client):
        """Test view returns 403 if not in scope"""
        url = _url(3)
        auth = hawk_auth_sender(
            url,
            key_id='no-scope-id',
            secret_key='no-scope-key',
        ).request_header

        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_key(self, api_client):
        """Test view returns 401 if the key is invalid"""
        url = _url(3)
        auth = hawk_auth_sender(
            url,
            key_id='invalid',
        ).request_header

        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_match_win_view_returns_an_empty_list(self, api_client):
        """Test export wins returns an empty list if no match is found."""
        url = _url(3)
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    def test_match_hvc_win_view(self, hvc_win, api_client):
        """Test export wins are returned in the expected format."""
        hvc, win = hvc_win
        business_potential_dict = dict(BUSINESS_POTENTIAL)
        url = _url(1)
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK

        assert response.json() == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': str(win.id),
                    'title': win.name_of_export,
                    'date': format_date_or_datetime(win.date.date()),
                    'created': format_date_or_datetime(win.created),
                    'country': 'Canada',
                    'sector': 'Construction',
                    'business_potential': business_potential_dict[win.business_potential],
                    'business_type': win.business_type,
                    'name_of_export': win.name_of_export,
                    'officer': {
                        'name': win.lead_officer_name,
                        'email': win.lead_officer_email_address,
                        'team': {
                            'type': win.team_type,
                            'sub_type': win.hq_team,
                        },
                    },
                    'contact': {
                        'name': win.customer_name,
                        'email': win.customer_email_address,
                        'job_title': win.customer_job_title,
                    },
                    'value': {
                        'export': {
                            'total': win.total_expected_export_value,
                            'breakdowns': [
                                {
                                    'year': breakdown.year,
                                    'value': breakdown.value,
                                } for breakdown in win.breakdowns.all()
                            ],
                        },
                    },
                    'customer': win.company_name,
                    'response': {
                        'confirmed': win.confirmation.agree_with_win,
                        'date': format_date_or_datetime(win.confirmation.created),
                    },
                    'hvc': {
                        'code': hvc.campaign_id,
                        'name': hvc.name,
                    },
                },
            ],
        }

    def test_match_non_hvc_win_view(self, non_hvc_win, api_client):
        """Test export wins are returned in the expected format."""
        win = non_hvc_win
        business_potential_dict = dict(BUSINESS_POTENTIAL)
        url = _url(1)
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK

        assert response.json() == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': str(win.id),
                    'title': win.name_of_export,
                    'date': format_date_or_datetime(win.date.date()),
                    'created': format_date_or_datetime(win.created),
                    'country': 'Canada',
                    'sector': 'Construction',
                    'business_potential': business_potential_dict[win.business_potential],
                    'business_type': win.business_type,
                    'name_of_export': win.name_of_export,
                    'officer': {
                        'name': win.lead_officer_name,
                        'email': win.lead_officer_email_address,
                        'team': {
                            'type': win.team_type,
                            'sub_type': win.hq_team,
                        },
                    },
                    'contact': {
                        'name': win.customer_name,
                        'email': win.customer_email_address,
                        'job_title': win.customer_job_title,
                    },
                    'value': {
                        'export': {
                            'total': win.total_expected_export_value,
                            'breakdowns': [
                                {
                                    'year': breakdown.year,
                                    'value': breakdown.value,
                                } for breakdown in win.breakdowns.all()
                            ],
                        },
                    },
                    'customer': win.company_name,
                    'response': {
                        'confirmed': win.confirmation.agree_with_win,
                        'date': format_date_or_datetime(win.confirmation.created),
                    },
                    'hvc': None,
                },
            ],
        }
