from rest_framework.generics import ListAPIView

from mi.models import ParentSector, SectorTeam
from mi.serializers import ParentSectorSerializer
from mi.views.base_view import MI_PERMISSION_CLASSES
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
    permission_classes = MI_PERMISSION_CLASSES
    queryset = SectorTeam.objects.all()
    serializer_class = ParentSectorSerializer
