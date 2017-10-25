import datetime

from django.utils.dateparse import parse_datetime, parse_date
from pytz import UTC
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, DateTimeField, empty
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.settings import api_settings
from rest_framework.utils import humanize_datetime

from .models import SectorTeam, OverseasRegion, ParentSector, OverseasRegionGroup


class SetorTeamSerializer(ModelSerializer):
    class Meta:
        model = SectorTeam
        fields = [
            'id',
            'name',
        ]


class OverseasRegionSerializer(ModelSerializer):
    class Meta:
        model = OverseasRegion
        fields = [
            'id',
            'name',
        ]


class OverseasRegionGroupSerializer(ModelSerializer):
    year = None
    regions = SerializerMethodField(method_name='regions_for_year')

    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop('year', None)
        super().__init__(*args, **kwargs)

    def regions_for_year(self, obj):
        qs = obj.regions.all()
        if self.year:
            qs = qs.filter(overseasregiongroupyear__financial_year=self.year)
        return [OverseasRegionSerializer(instance=x).data for x in qs.order_by('name')]

    class Meta:
        model = OverseasRegionGroup
        fields = [
            'id',
            'name',
            'regions'
        ]


class ParentSectorSerializer(ModelSerializer):
    class Meta:
        model = ParentSector
        fields = [
            'id',
            'name',
        ]


class DateTimeOrDateThatDefaultsTimeField(DateTimeField):

    default_time = None

    def __init__(self, default_time=None, format=empty, default_timezone=None, *args, **kwargs):
        self.default_time = default_time
        super().__init__(format=format, input_formats=None,
                         default_timezone=default_timezone, *args, **kwargs)

    def to_internal_value(self, value):
        input_formats = getattr(self, 'input_formats',
                                api_settings.DATETIME_INPUT_FORMATS)

        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            value = datetime.datetime.combine(
                value, self.default_time).replace(tzinfo=UTC)

        if isinstance(value, datetime.datetime):
            return self.enforce_timezone(value)

        try:
            parsed = parse_datetime(value)
        except (ValueError, TypeError):
            pass
        else:
            if parsed is not None:
                return self.enforce_timezone(parsed)
            else:
                try:
                    parsed = datetime.datetime.combine(
                        parse_date(value), self.default_time)
                except (ValueError, TypeError):
                    pass
                else:
                    if parsed is not None:
                        return self.enforce_timezone(parsed)

        humanized_format = humanize_datetime.datetime_formats(input_formats)
        self.fail('invalid', format=humanized_format)


class DateRangeSerializer(Serializer):

    date_start = DateTimeOrDateThatDefaultsTimeField(
        default_time=datetime.datetime.min.time(),
        required=False,
        write_only=True,
        default_timezone=UTC
    )

    date_end = DateTimeOrDateThatDefaultsTimeField(
        default_time=datetime.datetime.max.time(),
        required=False,
        write_only=True,
        default_timezone=UTC
    )

    def __init__(self, *args, **kwargs):
        self.financial_year = kwargs.pop('financial_year')
        super().__init__(*args, **kwargs)

    def validate_date_start(self, value):
        return self.is_inside_financial_year(value)

    def validate_date_end(self, value):
        return self.is_inside_financial_year(value)

    def is_inside_financial_year(self, value):
        end = self.financial_year.end
        start = self.financial_year.start
        if not end >= value >= start:
            raise ValidationError(
                "{value} must be in Financial Year: {fin_year}. Between {start} and {end}".format(
                    value=value,
                    fin_year=self.financial_year,
                    start=start,
                    end=end,
                )
            )
        return value
