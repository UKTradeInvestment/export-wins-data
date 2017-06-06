import datetime

from django.db import models

from django_countries.fields import CountryField

from wins.models import HVC


class OverseasRegion(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return 'OverseasRegion: {}'.format(self.name)

    @property
    def targets(self):
        """ List of `Targets` of all HVCs belonging to the `OverseasRegion` """

        targets = set()
        for country in self.countries.all():
            for target in country.targets.all():
                targets.add(target)
        return targets

    def fin_year_targets(self, fin_year):
        """ List of `Targets` of all HVCs belonging to the `OverseasRegion`, filtered by Financial Year """

        targets = set()
        for country in self.countries.all():
            for target in country.targets.filtered(fin_year):
                targets.add(target)
        return targets

    @property
    def campaign_ids(self):
        """ List of Campaign IDs of all HVCs belonging to the `OverseasRegion` """

        return [t.charcode for t in self.targets]

    def fin_year_campaign_ids(self, fin_year):
        """ List of Campaign IDs of all HVCs belonging to the `OverseasRegion`, filtered by Financial Year """

        return [t.campaign_id for t in self.fin_year_targets(fin_year)]

    @property
    def country_ids(self):
        """ List of all countries within the `OverseasRegion` """

        return [s.country for s in self.countries.all()]


class Country(models.Model):
    """
    Represents a DIT Country

    note that there may be few differences between DIT country names and django
    """

    country = CountryField(unique=True)
    overseas_region = models.ForeignKey(
        OverseasRegion,
        related_name='countries',
    )

    def __str__(self):
        return 'Country: {} ({})'.format(
            self.country.name,
            self.overseas_region,
        )


class SectorTeam(models.Model):
    """ A team in the business """

    name = models.CharField(max_length=128)

    def __str__(self):
        return 'SectorTeam: {}'.format(self.name)

    @property
    def sector_ids(self):
        """ List of CDMS sector IDs associated with the Sector Team """

        return [s.id for s in self.sectors.all()]

    @property
    def campaign_ids(self):
        """ List of Campaign IDs of all HVCs belonging to the Sector Team """

        return [t.charcode for t in self.targets.all()]

    def fin_year_campaign_ids(self, fin_year):
        """ List of Campaign IDs of all HVCs belonging to the HVC Group, filtered by Financial Year """

        return [t.charcode for t in self.targets.filter(financial_year=fin_year)]

    def fin_year_targets(self, fin_year):
        """ `Target` objects of `SectorTeam`, filtered by `FinancialYear` """
        return self.targets.filter(financial_year=fin_year)


class ParentSector(models.Model):
    """ CDMS groupings of CDMS Sectors """

    name = models.CharField(max_length=128)
    sector_team = models.ForeignKey(SectorTeam, related_name="parent_sectors")

    def __str__(self):
        return 'ParentSector: {} ({})'.format(self.name, self.sector_team)

    @property
    def sector_ids(self):
        """ List of CDMS sector IDs associated with the Parent Sector """

        return [s.id for s in self.sectors.all()]


class HVCGroup(models.Model):
    """ A group of individual HVCs

    e.g. there may be E003 France Agritech and E004 Spain Agritech, grouped
    into one grouping called Agritech.

    This is how Sector Teams organize their HVCs.

    Unrelated to ParentSectors or CDMS Sectors.
    """

    name = models.CharField(max_length=128)
    sector_team = models.ForeignKey(SectorTeam, related_name="hvc_groups")

    def __str__(self):
        return 'HVCGroup: {} ({})'.format(self.name, self.sector_team)

    @property
    def campaign_ids(self):
        """ List of Campaign IDs of all HVCs belonging to the HVC Group """

        return [t.charcode for t in self.targets.all()]

    def fin_year_campaign_ids(self, fin_year):
        """ List of Campaign IDs of all HVCs belonging to the HVC Group, filtered by Financial Year """

        return [t.charcode for t in self.targets.filter(financial_year=fin_year)]

    def fin_year_targets(self, fin_year):
        """ `Target` objects of `HVCGroup`, filtered by `FinancialYear` """
        return self.targets.filter(financial_year=fin_year)


class Sector(models.Model):
    """ CDMS big list of Sectors """

    # note, primary key matches ids of Win sector field (from constants)
    # note, there are 2 sectors in constants not in this

    name = models.CharField(max_length=128)
    sector_team = models.ManyToManyField(SectorTeam, related_name="sectors")
    parent_sector = models.ManyToManyField(ParentSector, related_name="sectors")

    def __str__(self):
        return 'Sector: {} ({})'.format(self.name, self.parent_sector)


class FinancialYear(models.Model):
    """ Financial Years """
    id = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=128)

    def __str__(self):
        return self.description

    @classmethod
    def current_fy(cls):
        now = datetime.datetime.now()
        if now.month < 4:
            return now.year - 1
        return now.year

    @classmethod
    def get_financial_start_date(cls, fin_year):
        """ Returns financial year start date for a given financial year

        Pass e.g. 2016 for the 2016/17 financial year

        """
        return datetime.datetime(fin_year, 4, 1)

    @classmethod
    def get_financial_end_date(cls, fin_year):
        """ Returns financial year end date for a given financial year

        Pass e.g. 2016 for the 2016/17 financial year

        """
        return datetime.datetime(fin_year + 1, 3, 31)

    @property
    def start(self):
        return FinancialYear.get_financial_start_date(self.id)

    @property
    def end(self):
        return FinancialYear.get_financial_end_date(self.id)

    @property
    def is_current(self):
        return self.id == FinancialYear.current_fy()


class Target(models.Model):
    """ HVC targets """

    campaign_id = models.CharField(max_length=4)
    target = models.BigIntegerField()
    sector_team = models.ForeignKey(SectorTeam, related_name="targets")
    hvc_group = models.ForeignKey(HVCGroup, related_name="targets")
    country = models.ForeignKey(Country, related_name="targets", null=True)
    financial_year = models.ForeignKey(FinancialYear, related_name="targets", null=False)

    @property
    def fy_digits(self):
        return str(self.financial_year_id)[-2:]

    @property
    def name(self):
        return HVC.objects.get(
            campaign_id=self.campaign_id,
            financial_year=str(self.financial_year.id)[-2:],
        ).name

    @property
    def charcode(self):
        return self.campaign_id + self.fy_digits

    def for_fin_year(self, fin_year):
        return self.objects.filter(financial_year=fin_year)

    def __str__(self):
        return 'Target: {} - {} - {}'.format(
            self.name,
            self.target,
            self.country,
        )
