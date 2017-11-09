from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

from django.db import models
from django.utils.timezone import now

from csvfiles.constants import FILE_TYPES
from users.models import User
from mi.models import FinancialYear


class File(models.Model):
    name = models.CharField(max_length=255)
    s3_path = models.CharField(max_length=255)
    user = models.ForeignKey(User, null=True)
    file_type = models.PositiveSmallIntegerField(choices=FILE_TYPES.choices)
    report_date = models.DateTimeField(default=now)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    metadata = JSONField(encoder=DjangoJSONEncoder, default={})

    def __str__(self):
        return 'file {} with path {} on {}'.format(
            self.name,
            self.s3_path,
            self.report_date
        )
