import csv
import sys
from tempfile import NamedTemporaryFile
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError

from csvfiles.constants import FILE_TYPES
from csvfiles.models import File as CSVFile
from wins.views import CurrentFinancialYearWins

from raven.contrib.django.raven_compat.models import client as sentry


class Command(BaseCommand):

    def upload_to_s3(self, file):
        """
        upload a file like object to s3

        :param file_: file to upload
        :return: full s3uri
        """
        now_ = now()

        file_name = 'export-wins/{year}/{month}/{timestamp}.csv'.format(
            year=now_.year,
            month=now_.month,
            timestamp=now_.isoformat()
        )

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_KEY_CSV_UPLOAD_ACCESS + '1',
            aws_secret_access_key=settings.AWS_SECRET_CSV_UPLOAD_ACCESS,
            region_name=settings.AWS_REGION_CSV
        )
        s3.upload_file(
            file,
            settings.AWS_BUCKET_CSV,
            file_name,
            ExtraArgs={'ServerSideEncryption': "AES256"}
        )
        return 's3://{bucket_name}/{key}'.format(
            bucket_name=settings.AWS_BUCKET_CSV,
            key=file_name
        )

    def handle(self, *args, **options):
        v = CurrentFinancialYearWins()
        csv_stream = v._make_flat_wins_csv_stream(
            v._make_flat_wins_csv())

        with NamedTemporaryFile(mode='w+') as ew_file:
            for line in csv_stream:
                ew_file.write(line)

            try:
                result = self.upload_to_s3(ew_file.name)

                CSVFile(
                    file_type=FILE_TYPES.EXPORT_WINS,
                    name='Export Wins Daily',
                    s3_path=result
                ).save()
            except (Boto3Error, ClientError):
                sentry.captureException(exc_info=sys.exc_info())
