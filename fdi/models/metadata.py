import uuid

from django.db.models import UUIDField
from django.db import models

from django_countries.fields import CountryField
from django_countries import Countries as DjCountries

from fdi.models.constants import MAX_LENGTH
from fdi.utils import datahub_country_iso_code


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

    def save(self, **kwargs):
        self.iso_code = datahub_country_iso_code(self.name)
        super().save(**kwargs)
