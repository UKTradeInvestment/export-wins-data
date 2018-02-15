from django.db import models

from fdi.models.metadata import (
    Country,
    FDIValue,
    Involvement,
    InvestmentType,
    Sector,
    SpecificProgramme,
    UKRegion,
)

from fdi.models.constants import MAX_LENGTH
from mi.models import FinancialYear


class InvestmentsQuerySet(models.QuerySet):

    def won(self):
        return self.filter(stage='won')

    def for_sector_team(self, sector_team):
        return self.filter(sector__in=sector_team.sectors.all())

    def verified(self):
        return self.filter(stage='verify win')

    def pipeline(self):
        return self.exclude(stage__in=['won', 'verify win'])

    def won_and_verify(self):
        return self.filter(stage__in=['won', 'verify win'])


class SectorTeam(models.Model):
    """ FDI's team structure that maps to Sectors """
    name = models.CharField(max_length=MAX_LENGTH, unique=True)
    description = models.CharField(max_length=MAX_LENGTH)
    sectors = models.ManyToManyField(Sector, through="SectorTeamSector")

    def __str__(self):
        return self.name


class SectorTeamSector(models.Model):
    """ SectorTeam to Sector mapping """
    team = models.ForeignKey(SectorTeam, on_delete=models.PROTECT)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT)

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

    market = models.ForeignKey(Market, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.market} - {self.country}'


class MarketGroup(models.Model):
    """ MI's representation of FDI MarketGroups """

    name = models.CharField(max_length=MAX_LENGTH, unique=True)
    countries = models.ManyToManyField(Country, through="MarketGroupCountry")

    def __str__(self):
        return self.name


class MarketGroupCountry(models.Model):
    """ One to many representation of MarketGroup and Country """

    market_group = models.ForeignKey(MarketGroup, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.market_group} - {self.country}'


class Investments(models.Model):
    """
    The model to query all MI data from
    """
    project_code = models.CharField(
        null=False, blank=False, db_index=True, max_length=MAX_LENGTH)

    stage = models.CharField(max_length=MAX_LENGTH)
    status = models.CharField(max_length=MAX_LENGTH, null=True)
    number_new_jobs = models.PositiveIntegerField(null=False, default=0)
    number_safeguarded_jobs = models.PositiveIntegerField(
        null=False, default=0)

    fdi_value = models.ForeignKey(FDIValue, null=True, on_delete=models.PROTECT)

    date_won = models.DateField(null=True)
    sector = models.ForeignKey(Sector, null=True, on_delete=models.PROTECT)
    uk_regions = models.ManyToManyField(UKRegion, through="InvestmentUKRegion")

    client_relationship_manager = models.CharField(max_length=MAX_LENGTH)
    client_relationship_manager_team = models.CharField(
        max_length=MAX_LENGTH, null=True)
    company_name = models.CharField(max_length=MAX_LENGTH)
    company_reference = models.CharField(max_length=MAX_LENGTH)
    company_country = models.ForeignKey(Country, null=True, on_delete=models.PROTECT)

    investment_value = models.BigIntegerField(default=0)
    foreign_equity_investment = models.BigIntegerField(default=0)

    level_of_involvement = models.ForeignKey(Involvement, null=True, on_delete=models.PROTECT)
    investment_type = models.ForeignKey(InvestmentType, null=True, on_delete=models.PROTECT)
    specific_program = models.ForeignKey(SpecificProgramme, null=True, on_delete=models.PROTECT)

    # set to true if importing from spreadsheet
    legacy = models.BooleanField(default=False, db_index=True)
    objects = InvestmentsQuerySet.as_manager()

    hvc_code = models.CharField(max_length=5, null=True)


class InvestmentUKRegion(models.Model):
    """ representation of UK regions that were benefiting from the investment"""

    investment = models.ForeignKey(Investments, on_delete=models.CASCADE)
    uk_region = models.ForeignKey(UKRegion, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.investment} - {self.uk_region}'


class GlobalTargets(models.Model):
    """ FDI type of investment based global targets per FY """

    financial_year = models.OneToOneField(FinancialYear, on_delete=models.PROTECT)
    high = models.PositiveIntegerField(null=False)
    good = models.PositiveIntegerField(null=False)
    standard = models.PositiveIntegerField(null=False)

    @property
    def total(self):
        return self.high + self.good + self.standard

    def __str__(self):
        return f'{self.financial_year.description} - h{self.high},g{self.good},s{self.standard},∑{self.total}'


class MarketTarget(models.Model):
    """ Targets for SectorTeam and Market combinations, per FY.
    Some of them are considered HVC, some non-HVC """

    sector_team = models.ForeignKey(SectorTeam, related_name="market_targets", on_delete=models.PROTECT)
    market = models.ForeignKey(Market, related_name="market_targets", on_delete=models.PROTECT)
    target = models.IntegerField(null=True)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.financial_year} - {self.sector_team}/{self.market}: non-HVC: {self.non_hvc_target}'


class SectorTeamTarget(models.Model):
    """ Targets for SectorTeam and Market combinations, per FY.
    Some of them are considered HVC, some non-HVC """

    hvc_code = models.CharField(max_length=5)
    sector_team = models.ForeignKey(SectorTeam, related_name="sector_targets", on_delete=models.PROTECT)
    market_group = models.ForeignKey(MarketGroup, related_name="sector_targets", on_delete=models.PROTECT)
    target = models.IntegerField(null=True)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.financial_year} - {self.sector_team}/{self.market_group}: ' \
            f'HVC: {self.hvc_target}'


class OverseasRegion(models.Model):
    name = models.CharField(max_length=MAX_LENGTH)
    markets = models.ManyToManyField(Market, through="OverseasRegionMarket")

    def __str__(self):
        return self.name


class OverseasRegionMarket(models.Model):
    """ One to many representation of OverseasRegion and Market """

    overseas_region = models.ForeignKey(OverseasRegion, on_delete=models.PROTECT)
    market = models.ForeignKey(Market, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.overseas_region} - {self.market}'
