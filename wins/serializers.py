from rest_framework.serializers import (
    CharField, ModelSerializer, SerializerMethodField
)
from .constants import WITH_OUR_SUPPORT
from .models import Win, Breakdown, Advisor, CustomerResponse


class WinSerializer(ModelSerializer):

    id = CharField(read_only=True)
    responded = SerializerMethodField()
    sent = SerializerMethodField()
    country_name = SerializerMethodField()
    type_display = SerializerMethodField()

    class Meta(object):
        model = Win
        fields = (
            "id",
            "user",
            "company_name",
            "cdms_reference",
            "customer_name",
            "customer_job_title",
            "customer_email_address",
            "customer_location",
            "business_type",
            "description",
            "name_of_customer",
            "name_of_export",
            "date",
            "country",
            "type",
            "total_expected_export_value",
            "total_expected_non_export_value",
            "total_expected_odi_value",
            "goods_vs_services",
            "sector",
            "is_prosperity_fund_related",
            "hvc",
            "hvo_programme",
            "has_hvo_specialist_involvement",
            "is_e_exported",
            "type_of_support_1",
            "type_of_support_2",
            "type_of_support_3",
            "associated_programme_1",
            "associated_programme_2",
            "associated_programme_3",
            "is_personally_confirmed",
            "is_line_manager_confirmed",
            "lead_officer_name",
            "lead_officer_email_address",
            "other_official_email_address",
            "line_manager_name",
            "team_type",
            "hq_team",
            "location",
            "created",
            "updated",
            "complete",
            "responded",
            "sent",
            "country_name",
            "type_display",
            "audit",
        )

    def _our_help(self, conf):
        return dict(WITH_OUR_SUPPORT)[conf.expected_portion_without_help]

    def get_responded(self, win):
        if not hasattr(win, 'confirmation'):
            return None
        return {
            'created': win.confirmation.created,
            'our_help': self._our_help(win.confirmation),
        }

    def get_sent(self, win):
        notifications = win.notifications.filter(type='c').order_by('created')
        if not notifications:
            return []
        return [n.created for n in notifications]

    def get_country_name(self, win):
        return win.get_country_display()

    def get_type_display(self, win):
        return win.get_type_display()

    def validate_user(self, value):
        return self.context["request"].user


class ChoicesSerializerField(SerializerMethodField):
    """ Read-only field return representation of model field with choices

    http://stackoverflow.com/questions/28945327/django-rest-framework-with-choicefield

    """
    def to_representation(self, value):
        method_name = 'get_{}_display'.format(self.field_name)
        method = getattr(value, method_name)
        return method()


class LimitedWinSerializer(ModelSerializer):

    id = CharField(read_only=True)
    type = ChoicesSerializerField()
    country = ChoicesSerializerField()
    customer_location = ChoicesSerializerField()
    goods_vs_services = ChoicesSerializerField()

    class Meta(object):
        model = Win
        fields = (
            "id",
            "description",
            "type",
            "date",
            "country",
            "customer_location",
            "total_expected_export_value",
            "total_expected_non_export_value",
            "total_expected_odi_value",
            "goods_vs_services",
            "created",
        )


class DetailWinSerializer(ModelSerializer):

    id = CharField(read_only=True)
    type = ChoicesSerializerField()
    country = ChoicesSerializerField()
    customer_location = ChoicesSerializerField()
    goods_vs_services = ChoicesSerializerField()
    sector = ChoicesSerializerField()
    hvc = ChoicesSerializerField()
    hvo_programme = ChoicesSerializerField()
    type_of_support_1 = ChoicesSerializerField()
    type_of_support_2 = ChoicesSerializerField()
    type_of_support_3 = ChoicesSerializerField()
    associated_programme_1 = ChoicesSerializerField()
    associated_programme_2 = ChoicesSerializerField()
    associated_programme_3 = ChoicesSerializerField()
    team_type = ChoicesSerializerField()
    hq_team = ChoicesSerializerField()
    breakdowns = SerializerMethodField()  # prob should be breakdownserializer
    advisors = SerializerMethodField()  # prob should be advisorserializer
    responded = SerializerMethodField()
    sent = SerializerMethodField()

    class Meta(object):
        model = Win
        fields = (
            "id",
            "company_name",
            "cdms_reference",
            "customer_name",
            "customer_job_title",
            "customer_email_address",
            "customer_location",
            "business_type",
            "description",
            "name_of_customer",
            "name_of_export",
            "date",
            "country",
            "type",
            "total_expected_export_value",
            "total_expected_non_export_value",
            "total_expected_odi_value",
            "goods_vs_services",
            "sector",
            "is_prosperity_fund_related",
            "hvc",
            "hvo_programme",
            "has_hvo_specialist_involvement",
            "is_e_exported",
            "type_of_support_1",
            "type_of_support_2",
            "type_of_support_3",
            "associated_programme_1",
            "associated_programme_2",
            "associated_programme_3",
            "is_personally_confirmed",
            "is_line_manager_confirmed",
            "lead_officer_name",
            "lead_officer_email_address",
            "other_official_email_address",
            "line_manager_name",
            "team_type",
            "hq_team",
            "location",
            "created",
            "updated",
            "complete",
            "breakdowns",
            "advisors",
            "responded",
            "sent",
        )

    def get_breakdowns(self, win):
        """ Should use breakdownserializer probably """

        exports = win.breakdowns.filter(type=1).order_by('year')
        exports = [{'value': b.value, 'year': b.year} for b in exports]
        nonexports = win.breakdowns.filter(type=2).order_by('year')
        nonexports = [{'value': b.value, 'year': b.year} for b in nonexports]
        odi = win.breakdowns.filter(type=3).order_by('year')
        odi = [{'value': b.value, 'year': b.year} for b in odi]
        return {
            'exports': exports,
            'nonexports': nonexports,
            'odi': odi,
        }

    def get_advisors(self, win):
        """ Should use advisorserializer probably """
        return [
            {
                'name': a.name,
                'team_type': a.get_team_type_display(),
                'hq_team': a.get_hq_team_display(),
                'location': a.location,
            }
            for a in win.advisors.all()
        ]

    def get_responded(self, win):
        # should be abstracted better
        if not hasattr(win, 'confirmation'):
            return None
        return {'created': win.confirmation.created}

    def get_sent(self, win):
        # should be abstracted better
        notifications = win.notifications.filter(type='c').order_by('created')
        if not notifications:
            return []
        return [n.created for n in notifications]


class BreakdownSerializer(ModelSerializer):

    class Meta(object):
        model = Breakdown
        fields = (
            "id",
            "win",
            "type",
            "year",
            "value"
        )


class AdvisorSerializer(ModelSerializer):

    class Meta(object):
        model = Advisor
        fields = (
            "id",
            "win",
            "name",
            "team_type",
            "hq_team",
            "location"
        )


class CustomerResponseSerializer(ModelSerializer):

    class Meta(object):
        model = CustomerResponse
        fields = (
            "win",
            "created",
            "name",
            "agree_with_win",
            "comments",
            "our_support",
            "access_to_contacts",
            "access_to_information",
            "improved_profile",
            "gained_confidence",
            "developed_relationships",
            "overcame_problem",
            "involved_state_enterprise",
            "interventions_were_prerequisite",
            "support_improved_speed",
            "expected_portion_without_help",
            "last_export",
            "company_was_at_risk_of_not_exporting",
            "has_explicit_export_plans",
            "has_enabled_expansion_into_new_market",
            "has_increased_exports_as_percent_of_turnover",
            "has_enabled_expansion_into_existing_market",
            "case_study_willing",
        )
