from django.db.models import Func, F, Sum, Count

from fdi.models import Investments
from core.views import BaseMIView
from mi.models import Sector


class BaseFDIView(BaseMIView):

    queryset = Investments.objects.all()

    def get_queryset(self):
        return self.queryset

    def get_results(self):
        return []

    def get(self, request):
        return self._success(self.get_results())


class FDISectorTeamListView(BaseFDIView):

    def get(self, request):
        all_sectors = Sector.objects.all().values()
        return self._success(all_sectors)


class FDISectorOverview(BaseFDIView):
    pass


class FDIOverview(BaseFDIView):
    pass


class FDIYearOnYearComparison(BaseFDIView):

    def get_results(self):
        return self.get_queryset().won().values(
            'date_won'
        ).annotate(
            year=Func(F('date_won'), function='get_financial_year')
        ).annotate(
            Count('year'),
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value')
        ).values(
            'year',
            'year__count',
            'number_new_jobs__sum',
            'number_safeguarded_jobs__sum',
            'investment_value__sum'
        ).order_by('year')
