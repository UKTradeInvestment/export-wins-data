from fdi.models import Investments
from core.views import BaseMIView
from mi.models import Sector


class BaseFDIView(BaseMIView):

    queryset = Investments.objects.all()

    def get_queryset(self):
        return self.queryset


class FDISectorTeamListView(BaseFDIView):

    def get(self, request):
        all_sectors = Sector.objects.all().values()
        return self._success(all_sectors)


class FDISectorOverview(BaseFDIView):
    pass


class FDIOverview(BaseFDIView):

    def get_results(self):
        return []

    def get(self, request):
        return self._success(self.get_results())
