from extended_choices import Choices

from django.db import models

from csv.constants import FILE_TYPES
from users.models import User


class File(models.Model):
    name = models.CharField(max_length=255)
    s3_path = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User)
    file_type = models.PositiveSmallIntegerField(choices=FILE_TYPES.choices)
    report_date = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return 'path {} created by {} on {}'.format(
            self.s3_path,
            self.user.get_username(),
            self.created
        )
