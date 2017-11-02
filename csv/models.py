from django.db import models

from users.models import User


class File(models.Model):
    s3_path = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    # type (type of file, ExportWins, FDI_Monthly, FDI_Daily etc)
    # report_date

    def __str__(self):
        return 'path {} created by {} on {}'.format(self.s3_path, self.user.get_username(), self.created)
