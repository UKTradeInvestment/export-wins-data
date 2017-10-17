from django.db.models import Func, F, Sum, Count, When, Case, Value, CharField, Max, Count
from django.db.models.functions import Coalesce

from core.utils import group_by_key
from fdi.models import (
    Investments,
    GlobalTargets,
    Sector,
    SectorTeam,
    Market,
    Target
)
from core.views import BaseMIView
from fdi.serializers import InvestmentsSerializer
from mi.utils import two_digit_float

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

    def get(self, request, *args, **kwargs):
        return self._success(self.get_results())

    def _get_fdi_summary(self):
        try:
            fdi_target = GlobalTargets.objects.get(financial_year=self.fin_year)
        except GlobalTargets.DoesNotExist:
            fdi_target = GlobalTargets(financial_year=self.fin_year, high=0, good=0, standard=0)

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

        formatted_breakdown_by_value = group_by_key([
            {
                **x,
                "target": getattr(fdi_target, x['value'], 0),
                "value__percent": two_digit_float((x['count'] / total) * 100)
            } for x in data
        ], key='value', flatten=True)

        return {
            "target": fdi_target.total,
            "performance": {
                "verified": formatted_breakdown_by_value if formatted_breakdown_by_value else None,
            },
            "total": {
                "verified": {
                    "number_new_jobs__sum": sum(x['number_new_jobs__sum'] for x in data),
                    "number_safeguarded_jobs__sum": sum(x['number_safeguarded_jobs__sum'] for x in data),
                    "investment_value__sum": sum(x['investment_value__sum'] for x in data),
                    "count": total
                },
                "pending": {k: v or 0 for k, v in pending.items()}
            },
            "verified_met_percent": two_digit_float(
                total / fdi_target.total * 100
            ) if fdi_target.total > 0 and total > 0 else 0.0

        }


class FDIBaseSectorTeamView(BaseFDIView):

    def initial(self, request, team_id, *args, **kwargs):
        self.team = self._get_team(team_id)
        if not self.team:
            return self._not_found(detail=f'team with id: {team_id} not found')
        super(FDIBaseSectorTeamView, self).initial(request, team_id, *args, **kwargs)

    def _get_team(self, team_id):
        """ Get SectorTeam object or False if invalid ID """
        try:
            return SectorTeam.objects.get(id=int(team_id))
        except SectorTeam.DoesNotExist:
            return False

    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(self._date_range_start(), self._date_range_end()))
        return qs.for_sector_team(self.team)

    def get_targets(self):
        return self.team.targets.filter(financial_year=self.fin_year)

    def get(self, request, *args, **kwargs):
        return super(FDIBaseSectorTeamView, self).get(request, *args, **kwargs)


class FDISectorTeamListView(BaseFDIView):

    def get(self, request, *args, **kwargs):
        all_sectors = SectorTeam.objects.all()
        formatted_sector_teams = [
            {
                'id': x.id,
                'name': x.name,
                'description': x.description,
                'sectors': x.sectors.all().values()
            } for x in all_sectors
        ]
        return self._success(formatted_sector_teams)


class FDISectorTeamOverview(BaseFDIView):
    pass


class FDIOverview(BaseFDIView):

    def get_results(self):
        return self._get_fdi_summary()


class FDISectorTeamListView(BaseFDIView):

    def get(self, request):
        all_sectors = Sector.objects.all().values()
        return self._success(all_sectors)


class FDISectorOverview(BaseFDIView):
    pass


class FDISectorTeamDetailView(FDIBaseSectorTeamView):
    team = None

    def _market_breakdown(self, investments, market, max_hvc_target):
        market_investments = investments.filter(company_country__in=market.countries.all())
        won_count = len([i for i in market_investments if i.stage == 'Won'])
        pending_count = len([i for i in market_investments if i.stage != 'Won'])
        try:
            target = Target.objects.get(sector_team=self.team, market=market)
        except Target.DoesNotExist:
            target = None

        market_data = {
            "name": market.name,
            "projects": {
                "number": won_count,
                "progress": two_digit_float(won_count * 100/max_hvc_target),
            },
            "pipeline": {
                "number": pending_count,
                "progress": two_digit_float(pending_count * 100/max_hvc_target),
            },
            "target": target.hvc_target if target else 0,
        }
        return market_data

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = self._get_fdi_summary()
        markets = Market.objects.all()
        max_hvc_target = Target.objects.filter(sector_team=self.team).aggregate(Max('hvc_target'))['hvc_target__max']
        market_data = [self._market_breakdown(investments_in_scope, market, max_hvc_target) for market in markets]

        results['markets'] = market_data
        return self._success(results)


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
                "year": y,
                **{b['value']: {
                    "count": b['year__count'],
                    "number_new_jobs__sum": b['number_new_jobs__sum'],
                    "number_safeguarded_jobs__sum": b['number_safeguarded_jobs__sum'],
                    "investment_value__sum": b['investment_value__sum']
                } for b in breakdown if b['year'] == y}
            } for y in year_buckets
        ]


class FDISectorTeamWinTable(FDIBaseSectorTeamView):

    def get_results(self):
        hvc_target = self.get_targets().aggregate(target=Coalesce(Sum('hvc_target'), 0))['target']
        non_hvc_target = self.get_targets().aggregate(target=Coalesce(Sum('non_hvc_target'), 0))['target']
        investments = InvestmentsSerializer(self.get_queryset(), many=True)

        return {
            "name": self.team.name,
            "description": self.team.description,
            "target": {
                "hvc": hvc_target,
                "non_hvc": non_hvc_target,
                "total": sum([hvc_target, non_hvc_target])
            },
            "investments": investments.data
        }
