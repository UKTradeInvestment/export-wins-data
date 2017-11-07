from django.contrib.auth import get_user_model
from rest_framework.fields import SerializerMethodField, CharField, ChoiceField, DateTimeField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator

from csvfiles.constants import FILE_TYPES
from csvfiles.models import File
from csvfiles.validators import is_valid_s3_url

User = get_user_model()


class FileTypeChoiceField(ChoiceField):

    def __init__(self, choices, **kwargs):
        choice_strings_to_values = {key: val[1] for key, val in FILE_TYPES.constants.items()}
        super(FileTypeChoiceField, self).__init__(choices, **kwargs)
        self.choice_strings_to_values = choice_strings_to_values

    def to_representation(self, value):
        if value in ('', None):
            return value
        return self.choices[value]


class FileSerializer(ModelSerializer):
    name = CharField(required=False, max_length=255)
    file_type = FileTypeChoiceField(FILE_TYPES, required=True, read_only=False)
    user_email = SerializerMethodField()
    user = PrimaryKeyRelatedField(write_only=True, queryset=User.objects.all(),
                                  required=False, allow_null=True, allow_empty=True)
    s3_path = CharField(max_length=255, validators=[
        UniqueValidator(queryset=File.objects.all()),
        is_valid_s3_url
    ], required=True)
    report_date = DateTimeField(allow_null=True, required=False)

    def get_file_type_display(self, obj):
        return obj.get_file_type_display()

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return None

    class Meta:
        model = File
        fields = [
            'id',
            'name',
            's3_path',
            'file_type',
            'user_email',
            'user',
            'created',
            'is_active',
            'metadata',
            'report_date'
        ]


class ExportWinsFileSerializer(FileSerializer):
    user = PrimaryKeyRelatedField(write_only=True, queryset=User.objects.all(),
                                  required=True, allow_null=False, allow_empty=False)
