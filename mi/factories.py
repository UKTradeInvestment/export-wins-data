import factory
import faker
from factory.fuzzy import FuzzyChoice
from django.db.models import Model

from .models import HVCGroup, OverseasRegion, Sector, SectorTeam, Target


class OverseasRegionFactory(factory.DjangoModelFactory):
    class Meta:
        model = OverseasRegion

    team_name = 'WestEastNorth Eurasia-Pacific'


class SectorTeamFactory(factory.DjangoModelFactory):
    class Meta:
        model = SectorTeam

    name = 'AgriInfraTechSpace & FinEnergy'


class TargetFactory(factory.DjangoModelFactory):
    class Meta:
        model = Target

    campaign_id = 'E001'
    target = FuzzyChoice(
        [0, 2000000, 5000000, 7000000, 9000000, 14000000, 17000000, 21000000]
    )


class HVCGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = HVCGroup

    name = 'FinBio-economy - Agritech'
    sector_team = factory.SubFactory(SectorTeamFactory)


class SectorFactory(factory.DjangoModelFactory):
    class Meta:
        model = Sector
    name = factory.Faker('sentence', nb_words=3, variable_nb_words=True)

    @factory.lazy_attribute
    def id(self):
        last = Sector.objects.order_by('id').last()
        if last:
            return int(last.pk) + 1
        else:
            return 1
