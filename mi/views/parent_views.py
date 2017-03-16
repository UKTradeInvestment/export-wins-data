from rest_framework.generics import ListAPIView

from alice.authenticators import IsMIServer, IsMIUser
from mi.models import ParentSector, SectorTeam
from mi.serializers import ParentSectorSerializer
from mi.views.sector_views import BaseSectorMIView


class BaseParentSectorMIView(BaseSectorMIView):
    """ Abstract Base for other Sector-related MI endpoints to inherit from """

    def _get_parent(self, parent_id):
        try:
            return ParentSector.objects.get(id=int(parent_id))
        except ParentSector.DoesNotExist:
            return False


class ParentSectorListView(ListAPIView):
    """
    List of all Parent Sectors
    """
    permission_classes = (IsMIServer, IsMIUser)
    queryset = SectorTeam.objects.all()
    serializer_class = ParentSectorSerializer
