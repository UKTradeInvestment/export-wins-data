import factory
from factory.fuzzy import FuzzyChoice

from .models import HVCGroup, OverseasRegion, SectorTeam, Target


class OverseasRegionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OverseasRegion

    team_name = 'WestEastNorth Eurasia-Pacific'


class SectorTeamFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SectorTeam

    name = 'AgriInfraTechSpace & FinEnergy'


class TargetFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Target

    campaign_id = 'E001'
    target = FuzzyChoice(
        [0, 2000000, 5000000, 7000000, 9000000, 14000000, 17000000, 21000000]
    )


class HVCGroupFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = HVCGroup

    name = 'FinBio-economy - Agritech'
    sector_team = factory.SubFactory(SectorTeamFactory)
