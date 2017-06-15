from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

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
