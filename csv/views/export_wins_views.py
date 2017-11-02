from operator import itemgetter
from urllib.parse import urlparse

import boto3

from django.conf import settings

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.authenticators import IsAdminServer, IsMIServer, IsMIUser
from ..models import File as CSVFile
from users.models import User


class ExportWinsCSVFile(APIView):
    """
    Helps storing file details of a file that was uploaded into S3
    Post creates a new entry
    Get returns all active entries from the database
    """
    permission_classes = (IsAdminUser, IsAdminServer)

    def post(self, request):
        path = request.data['path']
        user = User.objects.get(email=request.user.email)
        CSVFile.objects.create(s3_path=path, user=user)
        return Response({}, status=status.HTTP_201_CREATED)

    def get(self, request):
        files = CSVFile.objects.all()
        results = [
            {
                'id': csv_file.id,
                'path': csv_file.name,
                'user_email': csv_file.user.email,
                'created': csv_file.created
            }
            for csv_file in files
        ]
        return Response(sorted(results, key=itemgetter('created'), reverse=True), status=status.HTTP_200_OK)


class LatestExportWinsCSVFile(APIView):
    """
    Returns last uploaded file into S3
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        latest_csv_file = CSVFile.objects.latest('created')
        results = {
            'id': latest_csv_file.id,
            'created': latest_csv_file.created
        }
        return Response(results, status=status.HTTP_200_OK)


class GenerateOTUForExportWinsCSVFile(APIView):
    """
    This view generates a One Time URL for given file ID
    that was already uploaded into S3.
    """
    permission_classes = (IsMIServer, IsMIUser)

    def _generate_one_time_url(self, s3_path):
        """
        Generates presigned download url for a given full S3 path
        usual S3 file format is: s3://bucket_name/full/path
        """
        parsed = urlparse(s3_path)
        bucket = parsed.netloc
        file_key = parsed.path[1:]  # remove leading /

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_KEY_CSV_READ_ONLY_ACCESS,
            aws_secret_access_key=settings.AWS_SECRET_CSV_READ_ONLY_ACCESS,
            region_name=settings.AWS_REGION_CSV,
        )
        return s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket,
                'Key': file_key
            },
            # preserve it for 2 minutes
            ExpiresIn=120
        )

    def get(self, request, file_id):
        try:
            latest_csv_file = CSVFile.objects.get(id=file_id)
            results = {
                'id': latest_csv_file.id,
                'one_time_url': self._generate_one_time_url(latest_csv_file.s3_path)
            }

            return Response(results, status=status.HTTP_200_OK)
        except CSVFile.DoesNotExist:
            raise NotFound(detail='Invalid file ID')
