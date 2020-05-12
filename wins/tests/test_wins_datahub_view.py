from django.urls import reverse
from django.utils.http import urlencode

from fixturedb.factories.win import create_win_factory

import pytest

from rest_framework import status

from test_helpers.hawk_utils import hawk_auth_sender as _hawk_auth_sender

from wins.constants import BUSINESS_POTENTIAL, HQ_TEAM_REGION_OR_POST, TEAMS
from wins.factories import BreakdownFactory, HVCFactory, UserFactory
from wins.tests.utils import format_date_or_datetime


def _url(match_ids):
    encoded_params = urlencode({'match_id': ','.join(list(map(str, match_ids)))})
    path = f"{reverse('wins-by-match-id')}?{encoded_params}"
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
    """Test exports wins endpoint for data hub."""

    @pytest.mark.parametrize('verb', ('post', 'patch', 'delete'))
    def test_verbs_not_allowed(self, api_client, verb):
        """Test only get is supported."""
        url = _url([3])
        auth = hawk_auth_sender(url, method=verb).request_header
        response = getattr(api_client, verb)(
            url,
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_wrong_scope(self, api_client):
        """Test view returns 403 if not in scope."""
        url = _url([3])
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
        """Test view returns 401 if the key is invalid."""
        url = _url([3])
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

    def test_400_when_match_id_query_param_missing(self, api_client):
        """Test that 400 is returned when match id query param is missing."""
        url = 'http://testserver' + reverse('wins-by-match-id')
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_400_when_the_match_id_is_not_integer(self, api_client):
        """Test that 400 is returned when match id is not an integer."""
        url = _url(['a'])
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_400_when_one_of_the_match_ids_is_not_integer(self, api_client):
        """Test that 400 is returned when one of the match ids is not an integer."""
        url = _url([1, 'a'])
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_match_win_view_returns_an_empty_list(self, api_client):
        """Test export wins returns an empty list if no match is found."""
        url = _url([3])
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

    def test_match_hvc_win_view(self, api_client):
        """Test export wins are returned in the expected format."""
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
        business_potential_dict = dict(BUSINESS_POTENTIAL)
        teams_dict = dict(TEAMS)
        hq_dict = dict(HQ_TEAM_REGION_OR_POST)
        url = _url([1])
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
                            'type': teams_dict[win.team_type],
                            'sub_type': hq_dict[win.hq_team],
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

    def test_match_hvc_win_view_no_hvc(self, api_client):
        """Test export wins are returned in the expected format."""
        win = create_win_factory(UserFactory.create())(
            hvc_code='E083',
            sector_id=88,
            confirm=True,
        )
        BreakdownFactory.create(year=2020, win=win)
        BreakdownFactory.create(year=2021, win=win)
        business_potential_dict = dict(BUSINESS_POTENTIAL)
        teams_dict = dict(TEAMS)
        hq_dict = dict(HQ_TEAM_REGION_OR_POST)
        url = _url([1])
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
                            'type': teams_dict[win.team_type],
                            'sub_type': hq_dict[win.hq_team],
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

    def test_match_non_hvc_win_view(self, api_client):
        """Test export wins are returned in the expected format."""
        win = create_win_factory(UserFactory.create())(
            hvc_code=None,
            sector_id=88,
            confirm=True,
        )
        BreakdownFactory.create(year=2020, win=win)
        BreakdownFactory.create(year=2021, win=win)
        business_potential_dict = dict(BUSINESS_POTENTIAL)
        teams_dict = dict(TEAMS)
        hq_dict = dict(HQ_TEAM_REGION_OR_POST)
        url = _url([1])
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
                            'type': teams_dict[win.team_type],
                            'sub_type': hq_dict[win.hq_team],
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

    def test_match_hvc_win_view_non_existent_country(self, api_client):
        """Test export wins are returned in the expected format."""
        hvc = HVCFactory.create(
            campaign_id='E083',
            name='E083 - Consumer Goods & Retail',
            financial_year=16,
        )
        win = create_win_factory(UserFactory.create())(
            hvc_code='E083',
            sector_id=88,
            confirm=True,
            country='XY',
        )
        BreakdownFactory.create(year=2020, win=win)
        BreakdownFactory.create(year=2021, win=win)
        business_potential_dict = dict(BUSINESS_POTENTIAL)
        teams_dict = dict(TEAMS)
        hq_dict = dict(HQ_TEAM_REGION_OR_POST)
        url = _url([1])
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
                    'country': None,
                    'sector': 'Construction',
                    'business_potential': business_potential_dict[win.business_potential],
                    'business_type': win.business_type,
                    'name_of_export': win.name_of_export,
                    'officer': {
                        'name': win.lead_officer_name,
                        'email': win.lead_officer_email_address,
                        'team': {
                            'type': teams_dict[win.team_type],
                            'sub_type': hq_dict[win.hq_team],
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

    def test_match_hvc_win_view_null_business_potential(self, api_client):
        """Test export wins are returned in the expected format."""
        hvc = HVCFactory.create(
            campaign_id='E083',
            name='E083 - Consumer Goods & Retail',
            financial_year=16,
        )
        win = create_win_factory(UserFactory.create())(
            hvc_code='E083',
            sector_id=88,
            confirm=True,
            country='XY',
        )
        win.business_potential = None
        win.save()

        BreakdownFactory.create(year=2020, win=win)
        BreakdownFactory.create(year=2021, win=win)

        teams_dict = dict(TEAMS)
        hq_dict = dict(HQ_TEAM_REGION_OR_POST)
        url = _url([1])
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
                    'country': None,
                    'sector': 'Construction',
                    'business_potential': None,
                    'business_type': win.business_type,
                    'name_of_export': win.name_of_export,
                    'officer': {
                        'name': win.lead_officer_name,
                        'email': win.lead_officer_email_address,
                        'team': {
                            'type': teams_dict[win.team_type],
                            'sub_type': hq_dict[win.hq_team],
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

    def test_multiple_match_ids(self, api_client):
        """Test export wins are returned in the expected format."""
        HVCFactory.create(
            campaign_id='E083',
            name='E083 - Consumer Goods & Retail',
            financial_year=16,
        )
        hvc_win = create_win_factory(UserFactory.create())(
            hvc_code='E083',
            sector_id=88,
            confirm=True,
        )
        BreakdownFactory.create(year=2020, win=hvc_win)
        BreakdownFactory.create(year=2021, win=hvc_win)

        non_hvc_win = create_win_factory(UserFactory.create())(
            hvc_code=None,
            sector_id=88,
            confirm=True,
            match_id=2,
        )
        BreakdownFactory.create(year=2020, win=non_hvc_win)
        BreakdownFactory.create(year=2021, win=non_hvc_win)

        url = _url([1, 2])
        auth = hawk_auth_sender(url).request_header
        response = api_client.get(
            url,
            content_type='',
            HTTP_AUTHORIZATION=auth,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2
        assert response.json()['results'][0]['id'] == hvc_win.id
        assert response.json()['results'][1]['id'] == non_hvc_win.id
