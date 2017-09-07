from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import CASCADE
from django_extensions.db.fields import CreationDateTimeField


class ImportLog(models.Model):
    """
    Log of all imports, both full and partial
    """
    full = models.BooleanField(help_text='Is this a full import?')
    created = CreationDateTimeField('created')
    metadata = JSONField(help_text='Metadata about this import e.g request time, response size')


class InvestmentLoad(models.Model):
    """
    load raw data from Datahub's API
    """
    import_id = models.ForeignKey(ImportLog, on_delete=CASCADE)
    row_index = models.PositiveSmallIntegerField(blank=False, null=False)
    created = CreationDateTimeField('created')
    data = JSONField()

    class Meta:
        unique_together = ('import_id', 'row_index',)


class InvestmentLegacyLoad(models.Model):
    """
    From Tord's historical spreadsheets
    """
    filename = models.CharField(max_length=255)
    row_index = models.PositiveSmallIntegerField(blank=False, null=False)
    created = CreationDateTimeField('created')
    data = JSONField()
