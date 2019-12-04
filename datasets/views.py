from django.db.models import (
    Case, CharField, Count, OuterRef, Subquery, Value, When
)
from django.utils.decorators import method_decorator, decorator_from_middleware
from django_countries import countries
from rest_framework.views import APIView

from core.hawk import HawkAuthentication, HawkResponseMiddleware
from alice.middleware import alice_exempt
from datasets.pagination import WinsDatasetViewCursorPagination, DatasetViewCursorPagination

from wins.models import Win, Notification, CustomerResponse, Advisor, Breakdown, HVC


# Taken from data hubs query utils
# https://github.com/uktrade/data-hub-leeloo/blob/develop/datahub/core/query_utils.py
def get_choices_as_case_expression(model, field_name, lookup_field=None):
    """
    Gets an SQL expression that returns the display name for a field with choices.

    Usage example:
        InvestmentProject.objects.annotate(
            status_name=get_choices_as_case_expression(InvestmentProject, 'status'),
        )
    """
    field = model._meta.get_field(field_name)
    if lookup_field is None:
        lookup_field = field_name
    whens = (
        When(**{lookup_field: identifier}, then=Value(name)) for identifier, name in field.choices
    )
    return Case(*whens, output_field=CharField())


@method_decorator(alice_exempt, name='dispatch')
class DatasetView(APIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = ()
    pagination_class = DatasetViewCursorPagination

    @decorator_from_middleware(HawkResponseMiddleware)
    def get(self, request):
        """Endpoint returning all `Win` records"""
        paginator = self.pagination_class()
        win_data = self.get_dataset()
        page = paginator.paginate_queryset(win_data, request)
        return paginator.get_paginated_response(page)


class AdvisorsDatasetView(DatasetView):
    """
    API view providing 'GET' action returning advisers for consumption
    by data flow.
    """
    def get_dataset(self):
        return Advisor.objects.annotate(
            team_type_display=get_choices_as_case_expression(Advisor, 'team_type'),
            hq_team_display=get_choices_as_case_expression(Advisor, 'hq_team'),
        ).values(
            'hq_team_display',
            'hq_team',
            'id',
            'location',
            'name',
            'team_type_display',
            'team_type',
            'win__id',
        )


class BreakdownsDatasetView(DatasetView):
    """
    API view providing 'GET' action returning breakdowns for consumption
    by data flow.
    """
    def get_dataset(self):
        return Breakdown.objects.annotate(
            breakdown_type=get_choices_as_case_expression(Breakdown, 'type'),
        ).values(
            'id',
            'win__id',
            'breakdown_type',
            'year',
            'value',
        )


class HVCDatasetView(DatasetView):
    """
    API view providing 'GET' action returning HVC data for consumption
    by data flow.
    """
    def get_dataset(self):
        return HVC.objects.values(
            'campaign_id',
            'financial_year',
            'id',
            'name',
        )


class WinsDatasetView(DatasetView):
    """
    API view providing 'GET' action returning export wins for consumption
    by data flow.
    """
    pagination_class = WinsDatasetViewCursorPagination

    def get_dataset(self):
        notifications_queryset = Notification.objects.filter(
            win_id=OuterRef('pk'),
        ).order_by(
            'pk',
        )[:1]

        return Win.objects.annotate(
            associated_programme_1_display=get_choices_as_case_expression(
                Win,
                'associated_programme_1'
            ),
            associated_programme_2_display=get_choices_as_case_expression(
                Win,
                'associated_programme_2'
            ),
            associated_programme_3_display=get_choices_as_case_expression(
                Win,
                'associated_programme_3'
            ),
            associated_programme_4_display=get_choices_as_case_expression(
                Win,
                'associated_programme_4'
            ),
            associated_programme_5_display=get_choices_as_case_expression(
                Win,
                'associated_programme_5'
            ),
            business_potential_display=get_choices_as_case_expression(
                Win,
                'business_potential'
            ),
            confirmation_last_export=get_choices_as_case_expression(
                CustomerResponse,
                'last_export',
                lookup_field='confirmation__last_export'
            ),
            confirmation_marketing_source=get_choices_as_case_expression(
                CustomerResponse,
                'marketing_source',
                lookup_field='confirmation__marketing_source'
            ),
            confirmation_portion_without_help=get_choices_as_case_expression(
                CustomerResponse,
                'expected_portion_without_help',
                lookup_field='confirmation__expected_portion_without_help'
            ),
            country_name=Case(
                *[When(country=k, then=Value(v)) for k, v in countries],
                default=None,
                output_field=CharField()
            ),
            customer_email_date=Subquery(notifications_queryset.values('created')),
            customer_location_display=get_choices_as_case_expression(Win, 'customer_location'),
            export_experience_display=get_choices_as_case_expression(Win, 'export_experience'),
            goods_vs_services_display=get_choices_as_case_expression(Win, 'goods_vs_services'),
            hq_team_display=get_choices_as_case_expression(Win, 'hq_team'),
            hvo_programme_display=get_choices_as_case_expression(Win, 'hvo_programme'),
            num_notifications=Count('notifications'),
            sector_display=get_choices_as_case_expression(Win, 'sector'),
            team_type_display=get_choices_as_case_expression(Win, 'team_type'),
            type_of_support_1_display=get_choices_as_case_expression(Win, 'type_of_support_1'),
            type_of_support_2_display=get_choices_as_case_expression(Win, 'type_of_support_2'),
            type_of_support_3_display=get_choices_as_case_expression(Win, 'type_of_support_3'),
        ).order_by('created').values(
            'associated_programme_1_display',
            'associated_programme_2_display',
            'associated_programme_3_display',
            'associated_programme_4_display',
            'associated_programme_5_display',
            'audit',
            'business_potential_display',
            'business_type',
            'cdms_reference',
            'company_name',
            'complete',
            'confirmation__access_to_contacts',
            'confirmation__access_to_information',
            'confirmation__agree_with_win',
            'confirmation__case_study_willing',
            'confirmation__comments',
            'confirmation__company_was_at_risk_of_not_exporting',
            'confirmation__created',
            'confirmation__developed_relationships',
            'confirmation__gained_confidence',
            'confirmation__has_enabled_expansion_into_existing_market',
            'confirmation__has_enabled_expansion_into_new_market',
            'confirmation__has_explicit_export_plans',
            'confirmation__has_increased_exports_as_percent_of_turnover',
            'confirmation__improved_profile',
            'confirmation__interventions_were_prerequisite',
            'confirmation__involved_state_enterprise',
            'confirmation__name',
            'confirmation__other_marketing_source',
            'confirmation__our_support',
            'confirmation__overcame_problem',
            'confirmation__support_improved_speed',
            'confirmation_last_export',
            'confirmation_marketing_source',
            'confirmation_portion_without_help',
            'country',
            'country_name',
            'created',
            'customer_email_address',
            'customer_email_date',
            'customer_job_title',
            'customer_location_display',
            'customer_name',
            'date',
            'description',
            'export_experience_display',
            'goods_vs_services_display',
            'has_hvo_specialist_involvement',
            'hq_team_display',
            'hvc',
            'hvo_programme_display',
            'id',
            'is_e_exported',
            'is_line_manager_confirmed',
            'is_personally_confirmed',
            'is_prosperity_fund_related',
            'lead_officer_email_address',
            'lead_officer_name',
            'line_manager_name',
            'name_of_customer',
            'name_of_export',
            'num_notifications',
            'other_official_email_address',
            'sector_display',
            'team_type_display',
            'total_expected_export_value',
            'total_expected_non_export_value',
            'total_expected_odi_value',
            'type_of_support_1_display',
            'type_of_support_2_display',
            'type_of_support_3_display',
            'user__email',
            'user__name',
        )
