from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

from django.db import models
from django.utils.timezone import now

from csvfiles.constants import FILE_TYPES
from users.models import User


class File(models.Model):
    name = models.CharField(max_length=255)
    s3_path = models.CharField(max_length=255)
    user = models.ForeignKey(User, null=True)
    file_type = models.PositiveSmallIntegerField(choices=FILE_TYPES.choices)
    report_start_date = models.DateTimeField(default=now)
    report_end_date = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    metadata = JSONField(encoder=DjangoJSONEncoder, default={})

    def save(self, **kwargs):
        if not self.report_start_date:
            self.report_start_date = self.created
        if not self.report_end_date:
            self.report_end_date = self.report_start_date

        super(File, self).save(**kwargs)

    def __str__(self):
        return 'file {} with path {} from {} to {}'.format(
            self.name,
            self.s3_path,
            self.report_start_date,
            self.report_end_date
        )
