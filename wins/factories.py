import datetime

import factory
from factory.fuzzy import FuzzyChoice

from wins.models import (
    Advisor,
    Breakdown,
    CustomerResponse,
    HVC,
    Notification,
    Win,
)
from wins.constants import BUSINESS_POTENTIAL, SECTORS, WIN_TYPES
from users.factories import UserFactory


class WinFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Win

    user = factory.SubFactory(UserFactory)
    company_name = "company name"
    cdms_reference = "cdms reference"

    customer_name = "customer name"
    customer_job_title = "customer job title"
    customer_email_address = "customer@email.address"
    customer_location = 1

    description = "description"

    type = 1
    date = datetime.datetime(2016, 5, 25)
    country = "CA"

    business_potential = BUSINESS_POTENTIAL.MEDIUM_OR_HIGH.value

    total_expected_export_value = 100000
    goods_vs_services = 1
    total_expected_non_export_value = 2300
    total_expected_odi_value = 6400

    sector = FuzzyChoice(dict(SECTORS).keys())
    is_prosperity_fund_related = True
    hvo_programme = "AER-01"
    has_hvo_specialist_involvement = True
    is_e_exported = True

    type_of_support_1 = 1

    is_personally_confirmed = True
    is_line_manager_confirmed = True

    lead_officer_name = "lead officer name"
    line_manager_name = "line manager name"
    team_type = "team"
    hq_team = "team:1"
    complete = False


WIN_TYPES_DICT = {y: x for x, y in WIN_TYPES}


class HVCFactory(factory.DjangoModelFactory):

    class Meta:
        model = HVC

    campaign_id = factory.Sequence(lambda n: 'E%03d' % (n + 1))
    name = factory.LazyAttribute(lambda o: 'HVC: {}'.format(o.campaign_id))
    financial_year = FuzzyChoice([16, 17])


class BreakdownFactory(factory.DjangoModelFactory):

    class Meta:
        model = Breakdown

    type = WIN_TYPES_DICT['Export']
    year = 2016
    value = 182818284


class AdvisorFactory(factory.DjangoModelFactory):

    class Meta:
        model = Advisor

    name = 'Billy Bragg'
    team_type = 'dso'
    hq_team = 'team:1'


class CustomerResponseFactory(factory.DjangoModelFactory):

    class Meta:
        model = CustomerResponse

    our_support = 1
    access_to_contacts = 2
    access_to_information = 3
    improved_profile = 4
    gained_confidence = 5
    developed_relationships = 1
    overcame_problem = 2

    involved_state_enterprise = True
    interventions_were_prerequisite = False
    support_improved_speed = True
    expected_portion_without_help = 6
    last_export = 2
    company_was_at_risk_of_not_exporting = False
    has_explicit_export_plans = True
    has_enabled_expansion_into_new_market = False
    has_increased_exports_as_percent_of_turnover = True
    has_enabled_expansion_into_existing_market = False
    agree_with_win = FuzzyChoice([True, False])
    case_study_willing = False
    name = 'Cakes'
    comments = 'Good work'
    marketing_source = 1


class NotificationFactory(factory.DjangoModelFactory):

    class Meta:
        model = Notification

    recipient = 'a@b.com'
    type = 'c'
