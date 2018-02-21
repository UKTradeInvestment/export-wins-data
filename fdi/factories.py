import datetime

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDate
import faker

from fdi.models import (
    Country,
    Investments,
    InvestmentType,
    InvestmentUKRegion,
    Involvement,
    FDIValue,
    Sector,
    SpecificProgramme,
    UKRegion,
)

TEAMS = [
    '',
    'British Consulate General Milan Italy',
    'British Consulate General Sao Paulo Brazil',
    'British Consulate General Los Angeles USA',
    'British Embassy Tokyo Japan',
]

VALUE = [1000000, 2000000, 3000000, 4000000, 5000000]


class InvestmentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Investments

    project_code = ""

    stage = "won"
    status = "won"
    number_new_jobs = 10
    number_safeguarded_jobs = 10

    fdi_value = FuzzyChoice(FDIValue.objects.all())

    date_won = FuzzyDate(
        datetime.datetime(2017, 5, 27),
        datetime.datetime(2017, 5, 31)
        ).evaluate(2, None, False)
    sector = FuzzyChoice(Sector.objects.all())

    client_relationship_manager = 'client relationship manager'
    client_relationship_manager_team = FuzzyChoice(TEAMS)
    company_name = 'company name'
    company_reference = 'company reference'
    company_country = FuzzyChoice(Country.objects.all())

    investment_value = FuzzyChoice(VALUE)
    foreign_equity_investment = FuzzyChoice(VALUE)

    level_of_involvement = FuzzyChoice(Involvement.objects.exclude(name='No Involvement'))
    investment_type = FuzzyChoice(InvestmentType.objects.filter(name='FDI'))
    specific_program = FuzzyChoice(SpecificProgramme.objects.all())
