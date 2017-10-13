import uuid

from django.db.models import UUIDField
from django.db import models

from django_countries.fields import CountryField
from django_countries import Countries as DjCountries

from fdi.models.constants import MAX_LENGTH


class BaseMetadataModel(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=MAX_LENGTH)
    disabled_on = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        abstract = True


class Sector(BaseMetadataModel):
    pass


class UKRegion(BaseMetadataModel):
    pass


class Country(BaseMetadataModel):
    iso_code = CountryField(null=True)

    # this needs an pre_save method to set the iso code based on
    # the country name

    def try_set_iso_code(self):
        """
        Here are the list of country where there is a mismatch between
        Datahub data and Django Countries
        These needs a proper fix

        Aland Islands
        BLANK
        British Virgin Islands
        Burkina
        Burma
        Cape Verde
        Congo (Democratic Republic)
        East Timor
        Falkland Islands
        Gambia, The
        Heard Island and McDonald Island
        Hong Kong (SAR)
        Ivory Coast
        Korea (North)
        Korea (South)
        Macao (SAR)
        Micronesia
        Netherlands Antilles
        Occupied Palestinian Territories
        Pitcairn, Henderson, Ducie and Oeno Islands
        Reunion
        South Georgia and South Sandwich Islands
        St Barthelemy
        St Helena
        St Kitts and Nevis
        St Lucia
        St Martin
        St Pierre and Miquelon
        St Vincent
        Sudan, South
        Surinam
        Svalbard and Jan Mayen Islands
        TEST
        United States
        Vatican City
        Virgin Islands (US)
        """
        if self.name == "United States":
            dh_country_name = "United States of America"
        elif self.name == "Korea (South)":
            dh_country_name = "South Korea"
        elif self.name == "Hong Kong (SAR)":
            dh_country_name = "Hong Kong"
        else:
            dh_country_name = self.name

        code = DjCountries().by_name(dh_country_name)
        if code:
            self.iso_code = code

    def save(self, **kwargs):
        self.try_set_iso_code()
        super().save(**kwargs)
