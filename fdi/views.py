from django.db.models import Func, F, Sum, Count, When, Case, Value, CharField

from fdi.models import Investments, FDIGlobalTargets
from core.views import BaseMIView
from mi.models import Sector

ANNOTATIONS = dict(
    year=Func(F('date_won'), function='get_financial_year'),
    value=Case(
        When(approved_good_value=True, then=Value('good', output_field=CharField(max_length=10))),
        When(approved_high_value=True, then=Value('high', output_field=CharField(max_length=10))),
        default=Value('standard', output_field=CharField(max_length=10))
    )
)


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

        try:
            fdi_target = FDIGlobalTargets.objects.get(financial_year=self.fin_year)
        except FDIGlobalTargets.DoesNotExist:
            fdi_target = FDIGlobalTargets(financial_year=self.fin_year, high=0, good=0, standard=0)

        investments_in_scope = self.get_queryset().won().filter(
            date_won__range=(self._date_range_start(), self._date_range_end())
        )
        pending = self.get_queryset().filter(
            date_won=None
        ).exclude(
            stage='Won'
        ).aggregate(
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value'),
            count=Count('id'),
        )

        total = investments_in_scope.count()
        data = investments_in_scope.values(
            'approved_high_value', 'approved_good_value'
        ).annotate(
            value=ANNOTATIONS['value']
        ).annotate(
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value'),
            count=Count('value'),
        ).values(
            'value',
            'count',
            'number_new_jobs__sum',
            'number_safeguarded_jobs__sum',
            'investment_value__sum',
        )

        return {
            "target": fdi_target.total,
            "performance": {
                "verified": [
                    {
                        **x,
                        "target": getattr(fdi_target, x['value'], 0),
                        "value__percent": x['count'] / total
                    } for x in data
                ],
            },
            "total": {
                "verified": {
                    "number_new_jobs__sum": sum(x['number_new_jobs__sum'] for x in data),
                    "number_safeguarded_jobs__sum": sum(x['number_safeguarded_jobs__sum'] for x in data),
                    "investment_value__sum": sum(x['investment_value__sum'] for x in data),
                    "count": total
                },
                "pending": pending
            },
            "verified_met_percent": total / (total + pending['count'])
        }


class FDIYearOnYearComparison(BaseFDIView):

    def _fill_date_ranges(self):
        self.date_range = {
            "start": None,
            "end": self._date_range_end(),
        }

    def get_results(self):
        breakdown = self.get_queryset().won(
        ).filter(
            date_won__lt=self._date_range_end()
        ).values(
            'date_won'
        ).annotate(
            **ANNOTATIONS
        ).annotate(
            Count('year'),
            Count('value'),
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value')
        ).values(
            'year',
            'year__count',
            'number_new_jobs__sum',
            'number_safeguarded_jobs__sum',
            'investment_value__sum',
            'value',
            'value__count'
        ).order_by('year')
        year_buckets = sorted(list({x['year'] for x in breakdown}))
        return [
            {
                y: [{b['value']: {
                    "count": b['year__count'],
                    "number_new_jobs__sum": b['number_new_jobs__sum'],
                    "number_safeguarded_jobs__sum": b['number_safeguarded_jobs__sum'],
                    "investment_value__sum": b['investment_value__sum']
                }} for b in breakdown if b['year'] == y]
            } for y in year_buckets
        ]
