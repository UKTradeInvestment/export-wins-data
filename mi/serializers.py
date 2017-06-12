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

    regions = OverseasRegionSerializer(many=True)

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
