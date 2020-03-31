from rest_framework.serializers import (
    BooleanField,
    DateField,
    DateTimeField,
    CharField,
    ModelSerializer,
    SerializerMethodField
)
from .constants import EXPERIENCE_CATEGORIES, WITH_OUR_SUPPORT, BREAKDOWN_TYPES
from .models import Win, Breakdown, Advisor, CustomerResponse


class WinSerializer(ModelSerializer):

    id = CharField(read_only=True)
    responded = SerializerMethodField()
    sent = SerializerMethodField()
    country_name = SerializerMethodField()
    type_display = SerializerMethodField()
    export_experience_display = SerializerMethodField()

    class Meta(object):
        model = Win
        extra_kwargs = {
            'export_experience': {
                'choices': EXPERIENCE_CATEGORIES.active
            }
        }
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
            "associated_programme_4",
            "associated_programme_5",
            "is_personally_confirmed",
            "is_line_manager_confirmed",
            "lead_officer_name",
            "lead_officer_email_address",
            "other_official_email_address",
            "line_manager_name",
            "team_type",
            "hq_team",
            "business_potential",
            "export_experience",
            "location",
            "created",
            "updated",
            "complete",
            "responded",
            "sent",
            "country_name",
            "type_display",
            "export_experience_display",
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

    def get_export_experience_display(self, win):
        return win.get_export_experience_display() or ''


class ChoicesSerializerField(SerializerMethodField):
    """ Read-only field return representation of model field with choices

    http://stackoverflow.com/questions/28945327/django-rest-framework-with-choicefield

    requires there to be some choices

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
    export_experience_customer = SerializerMethodField()

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
            "export_experience_customer",
            "created",
        )

    def get_export_experience_customer(self, win):
        return win.get_export_experience_customer()


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
    associated_programme_4 = ChoicesSerializerField()
    associated_programme_5 = ChoicesSerializerField()
    team_type = ChoicesSerializerField()
    hq_team = ChoicesSerializerField()
    breakdowns = SerializerMethodField()  # prob should be breakdownserializer
    advisors = SerializerMethodField()  # prob should be advisorserializer
    responded = SerializerMethodField()
    sent = SerializerMethodField()
    business_potential_display = SerializerMethodField()
    export_experience_display = SerializerMethodField()

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
            "associated_programme_4",
            "associated_programme_5",
            "is_personally_confirmed",
            "is_line_manager_confirmed",
            "lead_officer_name",
            "lead_officer_email_address",
            "other_official_email_address",
            "line_manager_name",
            "team_type",
            "hq_team",
            "business_potential",
            "business_potential_display",
            "export_experience",
            "export_experience_display",
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

    def get_export_experience_display(self, win):
        return win.get_export_experience_display()

    def get_business_potential_display(self, win):
        return win.get_business_potential_display()


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
            "marketing_source",
            "other_marketing_source"
        )


class DataHubBreakdownSerializer(ModelSerializer):
    """Serialiser for CustomerResponse to expose confirmation status and date"""
    class Meta(object):
        model = Breakdown
        fields = (
            "year",
            "value"
        )
        read_only_fields = fields


class DataHubCustomerResponseSerializer(ModelSerializer):
    """Serialiser for CustomerResponse to expose confirmation status and date"""
    confirmed = BooleanField(source='agree_with_win', read_only=True)
    date = DateTimeField(source='created', read_only=True)

    class Meta(object):
        model = CustomerResponse
        fields = (
            'confirmed',
            'date'
        )
        read_only_fields = fields


class DataHubWinSerializer(ModelSerializer):
    """
    Read-only serialiser for the Hawk-authenticated win view.
    Win Serializer that will be consumed be used to display export wins in DataHub
    This is deisgned for datahub to proxy the api and should not need any more processing or transformation.
    """
    customer = CharField(source='company_name', read_only=True)
    hvc = SerializerMethodField(read_only=True)
    response = DataHubCustomerResponseSerializer(read_only=True, source='confirmation')
    officer = SerializerMethodField(read_only=True)

    contact = SerializerMethodField(read_only=True)
    value = SerializerMethodField(read_only=True)

    def get_value(self, win):
        """
        Return breakdown vaules in a value nested dict.
        Use only breakdown type EXPORT
        """
        breakdown_type = BREAKDOWN_TYPES[0]
        breakdowns_exports = win.breakdowns.filter(type=breakdown_type[0])
        breakdowns = DataHubBreakdownSerializer(breakdowns_exports, many=True)
        return {
            'export': {
                'value': win.total_expected_export_value,
                'breakdowns': breakdowns.data
            }
        }

    def get_officer(self, win):
        """Return lead officer in a officer nested dict."""
        return {
            'name': win.lead_officer_name,
            'email': win.lead_officer_email_address,
            'team': {
                'type': win.team_type,
                'sub_type': win.hq_team
            }
        }

    def get_hvc(self, win):
        """Return hvc data in a hvc nested dict."""
        return {
            'code': win.hvc,
            'name': win.hvo_programme,
        }

    def get_contact(self, win):
        """Return contact information in a contact nested dict."""
        return {
            'name': win.customer_name,
            'email': win.customer_email_address,
            'job_title': win.customer_job_title,
        }

    class Meta(object):
        model = Win
        fields = (
            'id',
            'date',
            'created',
            'country',
            'sector',
            'business_potential',
            'business_type',
            'name_of_export',
            'officer',
            'contact',
            'value',
            'customer',
            'response',
            'hvc',
        )
        read_only_fields = fields
