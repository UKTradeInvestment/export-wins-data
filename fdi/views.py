from django.db.models import Func, F, Sum, Count, When, Case, Value, CharField

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

    def get_results(self):
        investments_in_scope = self.get_queryset().won().filter(
            date_won__range=(self._date_range_start(), self._date_range_end())
        )
        total = investments_in_scope.count()
        data = investments_in_scope.values(
            'approved_high_value', 'approved_good_value'
        ).annotate(
            value=Case(
                When(approved_good_value=True, then=Value('good', output_field=CharField(max_length=10))),
                When(approved_high_value=True, then=Value('high', output_field=CharField(max_length=10))),
                default=Value('standard', output_field=CharField(max_length=10))
            )
        ).annotate(
            Count('value'),
        ).values(
            'value',
            'value__count'
        )

        return {
            "performance": [{
                "value": x['value'],
                "value__count": x['value__count'],
                "value__percent": '{0:.2%}'.format(x['value__count'] / total)
            } for x in data],
            "total": total
        }


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
