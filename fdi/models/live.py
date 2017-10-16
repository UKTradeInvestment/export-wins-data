from django.db import models

from fdi.models.metadata import Country, Sector, UKRegion
from fdi.models.constants import MAX_LENGTH
from mi.models import FinancialYear


class InvestmentsQuerySet(models.QuerySet):

    def won(self):
        return self.filter(stage='Won')


class SectorTeam(models.Model):
    """ FDI's team structure that maps to Sectors """
    name = models.CharField(max_length=MAX_LENGTH, unique=True)
    description = models.CharField(max_length=MAX_LENGTH)
    sectors = models.ManyToManyField(Sector, through="SectorTeamSector")

    def __str__(self):
        return self.name


class SectorTeamSector(models.Model):
    """ SectorTeam to Sector mapping """
    team = models.ForeignKey(SectorTeam)
    sector = models.ForeignKey(Sector)

    def __str__(self):
        return f'{self.team} - {self.sector}'


class Market(models.Model):
    """ MI's representation of FDI Markets """

    name = models.CharField(max_length=MAX_LENGTH, unique=True)
    countries = models.ManyToManyField(Country, through="MarketCountry")

    def __str__(self):
        return self.name


class MarketCountry(models.Model):
    """ One to many representation of Market and Country """

    market = models.ForeignKey('Market')
    country = models.ForeignKey(Country)

    def __str__(self):
        return f'{self.market} - {self.country}'


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
    sector = models.ForeignKey(Sector, null=True)
    uk_region = models.ForeignKey(UKRegion, null=True)

    client_relationship_manager = models.CharField(max_length=MAX_LENGTH)
    client_relationship_manager_team = models.CharField(
        max_length=MAX_LENGTH, null=True)
    company_name = models.CharField(max_length=MAX_LENGTH)
    company_reference = models.CharField(max_length=MAX_LENGTH)
    company_country = models.ForeignKey(Country, null=True)

    investment_value = models.BigIntegerField(default=0)
    foreign_equity_investment = models.BigIntegerField(default=0)

    # set to true if importing from spreadsheet
    legacy = models.BooleanField(default=False, db_index=True)
    objects = InvestmentsQuerySet.as_manager()


class GlobalTargets(models.Model):
    """ FDI type of investment based global targets per FY """

    financial_year = models.OneToOneField(FinancialYear)
    high = models.PositiveIntegerField(null=False)
    good = models.PositiveIntegerField(null=False)
    standard = models.PositiveIntegerField(null=False)

    @property
    def total(self):
        return self.high + self.good + self.standard

    def __str__(self):
        return f'{self.financial_year.description} - h{self.high},g{self.good},s{self.standard},∑{self.total}'


class Target(models.Model):
    """ Targets for Sector and Market combinations, per FY. Some of them are considered HVC """
    sector_team = models.ForeignKey(Sector, related_name="targets")
    market = models.ForeignKey(Market, related_name="targets")
    hvc_target = models.IntegerField()
    non_hvc_target = models.IntegerField()
    financial_year = models.OneToOneField(FinancialYear)

    def __str__(self):
        return f'{self.financial_year} - {self.sector_team}/{self.market}: ' \
            f'HVC: {self.hvc_target} non-HVC: {self.non_hvc_target}'
