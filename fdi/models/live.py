from django.db import models

from fdi.models.constants import MAX_LENGTH
from mi.models import FinancialYear


class InvestmentsQuerySet(models.QuerySet):

    def won(self):
        return self.filter(stage='Won')


class Investments(models.Model):
    """
    The model to query all MI data from
    """
    project_code = models.CharField(
        null=False, blank=False, db_index=True, max_length=MAX_LENGTH)

    stage = models.CharField(max_length=MAX_LENGTH)
    number_new_jobs = models.PositiveIntegerField(null=False, default=0)
    number_safeguarded_jobs = models.PositiveIntegerField(
        null=False, default=0)

    approved_high_value = models.BooleanField(default=False)
    approved_good_value = models.BooleanField(default=False)

    date_won = models.DateField(null=True)
    sector_team = models.CharField(max_length=MAX_LENGTH)
    uk_region = models.CharField(max_length=MAX_LENGTH)

    client_relationship_manager = models.CharField(max_length=MAX_LENGTH)
    client_relationship_manager_team = models.CharField(max_length=MAX_LENGTH, null=True)
    company_name = models.CharField(max_length=MAX_LENGTH)
    company_reference = models.CharField(max_length=MAX_LENGTH)
    company_country = models.CharField(max_length=MAX_LENGTH, null=True)

    investment_value = models.BigIntegerField(default=0)
    foreign_equity_investment = models.BigIntegerField(default=0)

    # set to true if importing from spreadsheet
    legacy = models.BooleanField(default=False, db_index=True)
    objects = InvestmentsQuerySet.as_manager()


class GlobalTargets(models.Model):
    financial_year = models.OneToOneField(FinancialYear)
    high = models.PositiveIntegerField(null=False)
    good = models.PositiveIntegerField(null=False)
    standard = models.PositiveIntegerField(null=False)

    @property
    def total(self):
        return self.high + self.good + self.standard

    def __str__(self):
        return f'{self.financial_year.description} - h{self.good},g{self.good},s{self.standard},∑{self.total}'
