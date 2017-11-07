from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from csv.models import File


class FileSerializer(ModelSerializer):

    file_type = SerializerMethodField('get_file_type_display')
    user_email = SerializerMethodField()

    def get_file_type_display(self, obj):
        return obj.get_file_type_display()

    def get_user_email(self, obj):
        return obj.user.email

    class Meta:
        model = File
        fields = [
            'id',
            'name',
            's3_path',
            'file_type',
            'user_email',
            'created',
            'is_active',
            'metadata'
        ]
