from datetime import datetime

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.fields import DateTimeField
from rest_framework.test import APIClient

from fixturedb.factories.win import create_win_factory
from test_helpers.hawk_utils import hawk_auth_sender as _hawk_auth_sender
from users.factories import UserFactory
from wins.factories import AdvisorFactory, BreakdownFactory, HVCFactory
from wins.models import CustomerResponse


@pytest.fixture
def api_client():
    return APIClient()


def hawk_auth_sender(url, **kwargs):
    """Pass credentials to hawk sender."""
    extra = {
        'key_id': 'data-flow-id',
        'secret_key': 'data-flow-key',
        **kwargs
    }
    return _hawk_auth_sender(url, **extra)


def multi_scope_hawk_auth_sender(url, **kwargs):
    """Pass multi scope hawk id is for backwards compatibilty."""
    extra = {
        'key_id': 'mulit-scope-id',
        'secret_key': 'mulit-scope-key',
        **kwargs
    }
    return _hawk_auth_sender(url, **extra)


def get_confirmation_attr_or_none(confirmation, field):
    if confirmation.id is None:
        return None
    if confirmation._meta.get_field(field).choices:
        return getattr(confirmation, 'get_{}_display'.format(field))()
    return getattr(confirmation, field)


class BaseDatasetViewSetTest:
    @pytest.mark.django_db
    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(self, api_client, method):
        """
        Test that only GET requests are allowed
        """
        response = getattr(api_client, method)(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(
                self.url,
                method=method.upper(),
            ).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.json() == {'detail': 'Method "{}" not allowed.'.format(method.upper())}

    @pytest.mark.django_db
    def test_no_data(self, api_client):
        """
        Test request completes successfully when no data is present
        """
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_no_scope(self, api_client):
        """
        Test request returns a 403 if keys are out of scope
        """
        auth_header = hawk_auth_sender(
            self.url,
            key_id='no-scope-id',
            secret_key='no-scope-key'
        ).request_header

        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=auth_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAdvisorsDatasetViewSet(BaseDatasetViewSetTest):
    """
    Tests for AdvisorsDatasetView
    """
    url = 'http://testserver' + reverse('datasets:advisors-dataset')
    url_incorrect_domain = 'http://incorrect' + reverse('datasets:advisors-dataset')
    url_incorrect_path = url + 'incorrect/'

    @staticmethod
    def _build_advisor_data(advisor):
        return {
            'id': advisor.id,
            'win__id': str(advisor.win.id),
            'name': advisor.name,
            'team_type': advisor.team_type,
            'hq_team': advisor.hq_team,
            'location': advisor.location,
            'team_type_display': advisor.get_team_type_display(),
            'hq_team_display': advisor.get_hq_team_display(),
        }

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'get_params,expected_json',
        (
            (
                # If no X-Forwarded-For header
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                }, {
                    'detail': 'Incorrect authentication credentials.'
                },
            ), (
                # If second-to-last X-Forwarded-For header isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If third-to-last IP in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If last of 3 IPs in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header isn't passed
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Authentication credentials were not provided.'},
            ), (
                # If the Authorization header generated from an incorrect ID
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url, key_id='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect secret
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url,
                        secret_key='incorrect'
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect domain
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url_incorrect_domain).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect path
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url_incorrect_path).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from incorrect content
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url, content='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_authentication(self, api_client, get_params, expected_json):
        response = api_client.get(self.url, content_type='', **get_params)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'hawk_auth_sender',
        (
            multi_scope_hawk_auth_sender,
            hawk_auth_sender
        )
    )
    def test_success(self, api_client, hawk_auth_sender):
        """
        Test that a single advisor is returned successfully
        """
        win = create_win_factory(UserFactory.create())(
            hvc_code='E083',
            confirm=True,
            export_value=10000000,
            win_date=datetime(2017, 3, 25),
            notify_date=datetime(2017, 3, 25),
            response_date=datetime(2017, 4, 5)
        )
        advisor = AdvisorFactory.create(
            win=win,
            name='UKTI SW',
            team_type='itt',
            hq_team='team:1',
        )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        assert len(results) == 1
        assert self._build_advisor_data(advisor) == results[0]

    @pytest.mark.django_db
    def test_multiple_records(self, api_client):
        """
        Test that a multiple advisors are returned successfully
        """
        with freeze_time('2019-01-01 01:03:00'):
            advisor1 = AdvisorFactory.create(
                win=create_win_factory(UserFactory.create())(
                    hvc_code='E001',
                    confirm=False,
                    export_value=88,
                    win_date=datetime(2018, 12, 12),
                    notify_date=datetime(2018, 11, 25),
                    response_date=datetime(2018, 12, 30)
                )
            )
        with freeze_time('2018-01-01 02:02:00'):
            advisor2 = AdvisorFactory.create(
                win=create_win_factory(UserFactory.create())(
                    hvc_code='E002',
                    confirm=True,
                    export_value=88,
                    win_date=datetime(2015, 12, 12),
                    notify_date=datetime(2016, 11, 25),
                    response_date=datetime(2017, 12, 30)
                )
            )
        with freeze_time('2017-01-01 03:01:00'):
            advisor3 = AdvisorFactory.create(
                win=create_win_factory(UserFactory.create())(
                    hvc_code='E003',
                    confirm=False,
                    export_value=88,
                    win_date=datetime(2014, 12, 12),
                    notify_date=datetime(2015, 11, 25),
                    response_date=datetime(2016, 12, 30)
                )
            )
            advisor4 = AdvisorFactory.create(
                win=create_win_factory(UserFactory.create())(
                    hvc_code='E004',
                    confirm=True,
                    export_value=88,
                    win_date=datetime(2017, 12, 12),
                    notify_date=datetime(2018, 11, 25),
                    response_date=datetime(2019, 12, 30)
                )
            )

        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response['results'] == [
            self._build_advisor_data(advisor1),
            self._build_advisor_data(advisor2),
            self._build_advisor_data(advisor3),
            self._build_advisor_data(advisor4)
        ]

    @pytest.mark.django_db
    def test_pagination(self, api_client):
        """
        Test that next property is set when number of objects is greater than threshold
        """
        AdvisorFactory.create_batch(
            101,
            win=create_win_factory(UserFactory.create())(
                hvc_code='E083',
                confirm=True,
                export_value=10000000,
                win_date=datetime(2017, 3, 25),
                notify_date=datetime(2017, 3, 25),
                response_date=datetime(2017, 4, 5)
            ),
            name='UKTI SW',
            team_type='itt',
            hq_team='team:1',
        )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None


class TestBreakdownsDatasetViewSet:
    """
    Tests for BreakdownsDatasetView
    """
    url = 'http://testserver' + reverse('datasets:breakdowns-dataset')
    url_incorrect_domain = 'http://incorrect' + reverse('datasets:breakdowns-dataset')
    url_incorrect_path = url + 'incorrect/'

    @staticmethod
    def _build_breakdown_data(breakdown):
        return {
            'id': breakdown.id,
            'breakdown_type': breakdown.get_type_display(),
            'value': breakdown.value,
            'win__id': str(breakdown.win.id),
            'year': breakdown.year,
        }

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'get_params,expected_json',
        (
            (
                # If no X-Forwarded-For header
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                }, {
                    'detail': 'Incorrect authentication credentials.'
                },
            ), (
                # If second-to-last X-Forwarded-For header isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If third-to-last IP in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If last of 3 IPs in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header isn't passed
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Authentication credentials were not provided.'},
            ), (
                # If the Authorization header generated from an incorrect ID
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url, key_id='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect secret
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url,
                        secret_key='incorrect'
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect domain
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url_incorrect_domain).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect path
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url_incorrect_path).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from incorrect content
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url, content='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_authentication(self, api_client, get_params, expected_json):
        response = api_client.get(self.url, content_type='', **get_params)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'hawk_auth_sender',
        (
            multi_scope_hawk_auth_sender,
            hawk_auth_sender
        )
    )
    def test_success(self, api_client, hawk_auth_sender):
        """
        Test that a single breakdown is returned successfully
        """
        win = create_win_factory(UserFactory.create())(
            hvc_code='E083',
            confirm=True,
            export_value=10000000,
            win_date=datetime(2017, 3, 25),
            notify_date=datetime(2017, 3, 25),
            response_date=datetime(2017, 4, 5)
        )
        breakdown = BreakdownFactory.create(
            win=win,
            year=2019,
            value=300000,
            type=1,
        )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        assert len(results) == 1
        assert self._build_breakdown_data(breakdown) == results[0]

    @pytest.mark.django_db
    def test_pagination(self, api_client):
        """
        Test that next property is set when number of objects is greater than threshold
        """
        BreakdownFactory.create_batch(
            101,
            win=create_win_factory(UserFactory.create())(
                hvc_code='E083',
                confirm=True,
                export_value=10000000,
                win_date=datetime(2017, 3, 25),
                notify_date=datetime(2017, 3, 25),
                response_date=datetime(2017, 4, 5)
            )
        )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None


class TestWinsDatasetViewSet:
    """
    Tests for WinsDatasetView
    """
    url = 'http://testserver' + reverse('datasets:wins-dataset')
    url_incorrect_domain = 'http://incorrect' + reverse('datasets:wins-dataset')
    url_incorrect_path = url + 'incorrect/'

    def _build_win_data(self, win):
        try:
            confirmation = win.confirmation
        except CustomerResponse.DoesNotExist:
            confirmation = CustomerResponse()
        return {
            'associated_programme_1_display': win.associated_programme_1,
            'associated_programme_2_display': win.associated_programme_2,
            'associated_programme_3_display': win.associated_programme_3,
            'associated_programme_4_display': win.associated_programme_4,
            'associated_programme_5_display': win.associated_programme_5,
            'audit': win.audit,
            'business_potential_display': win.get_business_potential_display(),
            'business_type': win.business_type,
            'cdms_reference': win.cdms_reference,
            'company_name': win.company_name,
            'complete': win.complete,
            'confirmation__access_to_contacts': confirmation.access_to_contacts,
            'confirmation__access_to_information': confirmation.access_to_information,
            'confirmation__agree_with_win': get_confirmation_attr_or_none(
                confirmation,
                'agree_with_win'
            ),
            'confirmation__case_study_willing': get_confirmation_attr_or_none(
                confirmation,
                'case_study_willing'
            ),
            'confirmation__comments': get_confirmation_attr_or_none(confirmation, 'comments'),
            'confirmation__company_was_at_risk_of_not_exporting': get_confirmation_attr_or_none(
                confirmation,
                'company_was_at_risk_of_not_exporting'
            ),
            'confirmation__created': DateTimeField().to_representation(
                confirmation.created
            ) if confirmation.id else None,
            'confirmation__developed_relationships': confirmation.developed_relationships,
            'confirmation__gained_confidence': confirmation.gained_confidence,
            'confirmation__has_enabled_expansion_into_existing_market': get_confirmation_attr_or_none(
                confirmation,
                'has_enabled_expansion_into_existing_market'
            ),
            'confirmation__has_enabled_expansion_into_new_market': get_confirmation_attr_or_none(
                confirmation,
                'has_enabled_expansion_into_new_market'
            ),
            'confirmation__has_explicit_export_plans': get_confirmation_attr_or_none(
                confirmation,
                'has_explicit_export_plans'
            ),
            'confirmation__has_increased_exports_as_percent_of_turnover': get_confirmation_attr_or_none(
                confirmation,
                'has_increased_exports_as_percent_of_turnover'
            ),
            'confirmation__improved_profile': confirmation.improved_profile,
            'confirmation__interventions_were_prerequisite': get_confirmation_attr_or_none(
                confirmation,
                'interventions_were_prerequisite'
            ),
            'confirmation__involved_state_enterprise': get_confirmation_attr_or_none(
                confirmation,
                'involved_state_enterprise'
            ),
            'confirmation__name': get_confirmation_attr_or_none(confirmation, 'name'),
            'confirmation__other_marketing_source': get_confirmation_attr_or_none(
                confirmation,
                'other_marketing_source'
            ),
            'confirmation__our_support': confirmation.our_support,
            'confirmation__overcame_problem': confirmation.overcame_problem,
            'confirmation__support_improved_speed': get_confirmation_attr_or_none(
                confirmation,
                'support_improved_speed'
            ),
            'confirmation_last_export': get_confirmation_attr_or_none(confirmation, 'last_export'),
            'confirmation_marketing_source': get_confirmation_attr_or_none(
                confirmation,
                'marketing_source'
            ),
            'confirmation_portion_without_help': get_confirmation_attr_or_none(
                confirmation,
                'expected_portion_without_help'
            ),
            'country': str(win.country),
            'country_name': win.country.name,
            'created': DateTimeField().to_representation(win.created),
            'customer_email_address': win.customer_email_address,
            'customer_email_date': DateTimeField().to_representation(
                win.notifications.first().created) if win.notifications.exists() else None,
            'customer_job_title': win.customer_job_title,
            'customer_location_display': win.get_customer_location_display(),
            'customer_name': win.customer_name,
            'date': datetime.strftime(win.date, '%Y-%m-%d'),
            'description': win.description,
            'export_experience_display': win.get_export_experience_display(),
            'goods_vs_services_display': win.get_goods_vs_services_display(),
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hq_team_display': win.get_hq_team_display(),
            'hvc': win.hvc,
            'hvo_programme_display': win.get_hvo_programme_display(),
            'id': str(win.id),
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': win.is_line_manager_confirmed,
            'is_personally_confirmed': win.is_personally_confirmed,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer_email_address': win.lead_officer_email_address,
            'lead_officer_name': win.lead_officer_name,
            'line_manager_name': win.line_manager_name,
            'name_of_customer': win.name_of_customer,
            'name_of_export': win.name_of_export,
            'num_notifications': win.notifications.count(),
            'other_official_email_address': win.other_official_email_address,
            'sector_display': win.get_sector_display(),
            'team_type_display': win.get_team_type_display(),
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'type_of_support_1_display': win.get_type_of_support_1_display(),
            'type_of_support_2_display': win.get_type_of_support_2_display(),
            'type_of_support_3_display': win.get_type_of_support_3_display(),
            'user__email': win.user.email,
            'user__name': win.user.name,
        }

    # Test no hawk auth
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'get_params,expected_json',
        (
            (
                # If no X-Forwarded-For header
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                }, {
                    'detail': 'Incorrect authentication credentials.'
                },
            ), (
                # If second-to-last X-Forwarded-For header isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If third-to-last IP in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If last of 3 IPs in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header isn't passed
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Authentication credentials were not provided.'},
            ), (
                # If the Authorization header generated from an incorrect ID
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url,
                        key_id='incorrect'
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect secret
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url,
                        secret_key='incorrect'
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect domain
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url_incorrect_domain,
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect path
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url_incorrect_path,
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from incorrect content
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url,
                        content='incorrect',
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_authentication(self, api_client, get_params, expected_json):
        response = api_client.get(self.url, content_type='', **get_params)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'hawk_auth_sender',
        (
            multi_scope_hawk_auth_sender,
            hawk_auth_sender
        )
    )
    def test_success(self, api_client, hawk_auth_sender):
        """
        Test that a single win is returned successfully
        """
        user = UserFactory.create()
        win = create_win_factory(user)(
            hvc_code='E083',
            confirm=True,
            export_value=10000000,
            win_date=datetime(2017, 3, 25),
            notify_date=datetime(2017, 3, 25),
            response_date=datetime(2017, 4, 5)
        )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        assert len(results) == 1
        assert self._build_win_data(win) == results[0]

    @pytest.mark.django_db
    def test_multiple_records(self, api_client):
        """
        Test that a multiple wins are returned successfully
        """
        with freeze_time('2019-01-01 01:03:00'):
            win1 = create_win_factory(UserFactory.create())(
                hvc_code='E001',
                confirm=False,
                export_value=88,
                win_date=datetime(2018, 12, 12),
                notify_date=datetime(2018, 11, 25),
                response_date=datetime(2018, 12, 30)
            )
        with freeze_time('2019-01-01 01:00:00'):
            win2 = create_win_factory(UserFactory.create())(
                hvc_code='E002',
                confirm=True,
                export_value=88,
                win_date=datetime(2015, 12, 12),
                notify_date=datetime(2016, 11, 25),
                response_date=datetime(2017, 12, 30)
            )
        with freeze_time('2017-01-01 03:01:00'):
            user = UserFactory.create()
            win3 = create_win_factory(user)(
                hvc_code='E003',
                confirm=False,
                export_value=88,
                win_date=datetime(2014, 12, 12),
                notify_date=datetime(2015, 11, 25),
                response_date=datetime(2016, 12, 30)
            )
            win4 = create_win_factory(user)(
                hvc_code='E004',
                confirm=True,
                export_value=88,
                win_date=datetime(2017, 12, 12),
                notify_date=datetime(2018, 11, 25),
                response_date=datetime(2019, 12, 30)
            )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        expected = sorted([win3, win4], key=lambda x: x.pk) + [win2, win1]
        for index, win in enumerate(expected):
            assert self._build_win_data(win) == results[index]

    @pytest.mark.django_db
    def test_pagination(self, api_client):
        """
        Test that next property is set when number of objects is greater than threshold
        """
        for _ in range(101):
            create_win_factory(UserFactory.create())(
                hvc_code='E083',
                confirm=True,
                export_value=10000000,
                win_date=datetime(2017, 3, 25),
                notify_date=datetime(2017, 3, 25),
                response_date=datetime(2017, 4, 5)
            )
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None


class TestHVCDatasetViewSet:
    """
    Tests for HVCDatasetView
    """
    url = 'http://testserver' + reverse('datasets:hvc-dataset')
    url_incorrect_domain = 'http://incorrect' + reverse('datasets:hvc-dataset')
    url_incorrect_path = url + 'incorrect/'

    @staticmethod
    def _build_hvc_data(hvc):
        return {
            'campaign_id': hvc.campaign_id,
            'financial_year': hvc.financial_year,
            'id': hvc.id,
            'name': hvc.name,
        }

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'get_params,expected_json',
        (
            (
                # If no X-Forwarded-For header
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                }, {
                    'detail': 'Incorrect authentication credentials.'
                },
            ), (
                # If second-to-last X-Forwarded-For header isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the only IP address in X-Forwarded-For isn't whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If third-to-last IP in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If last of 3 IPs in X-Forwarded-For header is whitelisted
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url).request_header,
                    'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header isn't passed
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Authentication credentials were not provided.'},
            ), (
                # If the Authorization header generated from an incorrect ID
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url, key_id='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect secret
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(
                        url,
                        secret_key='incorrect'
                    ).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect domain
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url_incorrect_domain).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from an incorrect path
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url_incorrect_path).request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ), (
                # If the Authorization header generated from incorrect content
                {
                    'HTTP_AUTHORIZATION': hawk_auth_sender(url, content='incorrect').request_header,
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_authentication(self, api_client, get_params, expected_json):
        response = api_client.get(self.url, content_type='', **get_params)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'hawk_auth_sender',
        (
            multi_scope_hawk_auth_sender,
            hawk_auth_sender
        )
    )
    def test_success(self, api_client, hawk_auth_sender):
        """
        Test that a single breakdown is returned successfully
        """
        hvc = HVCFactory.create()
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        assert len(results) == 1
        assert self._build_hvc_data(hvc) == results[0]

    @pytest.mark.django_db
    def test_pagination(self, api_client):
        """
        Test that next property is set when number of objects is greater than threshold
        """
        HVCFactory.create_batch(101)
        response = api_client.get(
            self.url,
            content_type='',
            HTTP_AUTHORIZATION=hawk_auth_sender(self.url).request_header,
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None
