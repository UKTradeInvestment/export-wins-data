import itertools
from typing import List

from collections import defaultdict

from django.db.models import Func, F, Q, Sum, When, Case, Value, CharField, Count, BooleanField
from django.db.models.functions import Coalesce
from django.db import connection
import django_filters.rest_framework as filters

from core.utils import group_by_key, getitem_or_default
from fdi.models import (
    Investments,
    SectorTeam,
    Market,
    SectorTeamTarget,
    MarketTarget,
    Country,
)
from core.views import BaseMIView
from fdi.serializers import InvestmentsSerializer
from mi.utils import two_digit_float, percentage_formatted

ANNOTATIONS = dict(
    year=Func(F('date_won'), function='get_financial_year'),
    value=Case(
        When(fdi_value='38e36c77-61ad-4186-a7a8-ac6a1a1104c6', then=Value(
            'high', output_field=CharField(max_length=10))),
        When(fdi_value='002c18d9-f5c7-4f3c-b061-aee09fce8416', then=Value(
            'good', output_field=CharField(max_length=10))),
        When(fdi_value='2bacde8d-128f-4d0a-849b-645ceafe4cf9', then=Value(
            'standard', output_field=CharField(max_length=10))),
        default=Value('unknown', output_field=CharField(max_length=10))
    ),
    is_hvc=Case(
        When(hvc_code__isnull=False, then=Value(True, output_field=BooleanField())),
        default=Value(False, output_field=BooleanField())
    )
)


def classify_stage(investment):
    if investment.stage == 'verify win':
        return 'verified'
    elif investment.stage == 'won':
        return 'confirmed'
    else:
        return 'pipeline'


def fill_in_missing(data, keys, defaults):
    for k in keys:
        if not data.get(k):
            data[k] = defaults
    return data


def fill_in_missing_performance(data):
    """
    takes a dict of performance dicts e.g. {'high'; {..}
    and fills in the missing if there is no good/standard/high key
    in the dictionary.
    """
    keys = ['high', 'good', 'standard']
    defaults = {
        "count": 0,
        "hvc_count": 0,
        "non_hvc_count": 0,
        "jobs_new": 0,
        "jobs_safeguarded": 0,
        "jobs_total": 0,
    }

    return fill_in_missing(data, keys, defaults)


def fill_in_missing_stages(data):
    return fill_in_missing(
        data,
        ['won', 'prospect', 'active', 'assign pm', 'verify win'],
        {'count': 0, 'percent': 0},
    )


def classify_quality(investment):
    if investment.fdi_value:
        if investment.fdi_value.id == '38e36c77-61ad-4186-a7a8-ac6a1a1104c6':
            return 'high'
        elif investment.fdi_value.id == '002c18d9-f5c7-4f3c-b061-aee09fce8416':
            return 'good'
        elif investment.fdi_value.id == '2bacde8d-128f-4d0a-849b-645ceafe4cf9':
            return 'standard'

    return 'unknown'


def make_nested(perf_by_value):
    total = sum([x['count'] for x in perf_by_value.values()])
    ret = {}
    for key, perf in perf_by_value.items():
        ret[key] = {
            "count": perf['count'],
            "percent": percentage_formatted(perf['count'], total),
            "campaign": {
                "hvc": {
                    "count": perf['hvc_count'],
                    "percent": percentage_formatted(perf['hvc_count'], perf['count'])
                },
                "non_hvc": {
                    "count": perf['non_hvc_count'],
                    "percent": percentage_formatted(perf['non_hvc_count'], perf['count'])
                }
            },
            "jobs": {
                "new": perf['jobs_new'],
                "safeguarded": perf['jobs_safeguarded'],
                "total": perf['jobs_total']
            }
        }
    return ret


def add_is_on_target(data):
    high_percent = data['high']['percent']
    high_and_good_percent = high_percent + data['good']['percent']
    data['high']['on_target'] = high_percent > 40
    data['good']['on_target'] = high_and_good_percent > 70
    data['standard']['on_target'] = False
    return data


def replace_spaces_with_underscore(text):
    return text.replace(' ', '_')


def investments_breakdown_by_stage(qs):
    data = qs.values(
        'stage'
    ).annotate(
        count=Count('stage'),
    ).values(
        'stage', 'count'
    )
    grouped = group_by_key(list(data), 'stage', flatten=True)
    total = sum((x['count'] for x in grouped.values()))
    for v in grouped.values():
        v['percent'] = percentage_formatted(v['count'], total)

    return {
        replace_spaces_with_underscore(k): v
        for k, v
        in fill_in_missing_stages(grouped).items()
    }


class SectorTeamFilter(filters.NumberFilter):

    def filter(self, qs, value):
        if not value:
            return qs

        try:
            sector_team = SectorTeam.objects.get(pk=value)
            return qs.filter(sector__in=sector_team.sectors.all())
        except SectorTeam.DoesNotExist:
            return qs.none()


class InvestmentsFilterSet(filters.FilterSet):

    quality = filters.CharFilter(field_name='fdi_value__name', lookup_expr='iexact')
    sector_team = SectorTeamFilter(field_name='sector')

    class Meta:
        model = Investments
        fields = ('quality', 'sector_team',)


class BaseFDIView(BaseMIView):

    queryset = Investments.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = InvestmentsFilterSet

    def get_queryset(self):
        """
        Exclude projects that have no DIT involvement (level_of_involvement: No Involvement)
        Include Project only of FDI type, NOT non-FDI and NOT Commitment to Invest. (investment_type: FDI)
        """
        return self.queryset.filter(
            ~Q(level_of_involvement__name='No Involvement'), investment_type__name='FDI'
        ).filter(
            date_won__range=(self._date_range_start(), self._date_range_end())
        )

    def get_results(self):
        return []

    def get(self, request, *args, **kwargs):
        return self._success(self.get_results())

    def _get_target(self):
        raise NotImplementedError()

    def _get_fdi_summary(self):
        investments_in_scope = self.filter_queryset(self.get_queryset())
        won_and_verify = investments_in_scope.won_and_verify()
        pipeline_active = investments_in_scope.filter(stage='active')

        won_and_verify_dict = self.performance_for_qs(won_and_verify)
        pipeline_active_dict = self.performance_for_qs(pipeline_active)

        return {
            "wins": won_and_verify_dict,
            "pipeline": {
                "active": pipeline_active_dict
            },
            "stages": investments_breakdown_by_stage(investments_in_scope)
        }

    def performance_for_qs(self, won_and_verify):
        won_and_verify_count = won_and_verify.count()
        stage_breakdown = investments_breakdown_by_stage(won_and_verify)
        total_value = won_and_verify.aggregate(
            total_investment_value__sum=Coalesce(Sum('investment_value'), Value(0))
        )
        jobs = won_and_verify.aggregate(
            new=Coalesce(Sum('number_new_jobs'), Value(0)),
            safeguarded=Coalesce(Sum('number_safeguarded_jobs'), Value(0)),
            total=Coalesce(Sum(F('number_new_jobs') + F('number_safeguarded_jobs')), Value(0))
        )

        campaign = getitem_or_default(won_and_verify.values(
            'hvc_code'
        ).annotate(
            is_hvc=ANNOTATIONS['is_hvc'],
            hvc_count=Count('is_hvc', filter=Q(is_hvc=True)),
            non_hvc_count=Count('is_hvc', filter=Q(is_hvc=False)),
        ).values(
            'hvc_count',
            'non_hvc_count'
        ), 0, {
            'hvc_count': 0,
            'non_hvc_count': 0
        })
        campaign_total = campaign['hvc_count'] + campaign['non_hvc_count']

        assert campaign_total == won_and_verify_count

        performance = won_and_verify.values(
            'fdi_value__name'
        ).annotate(
            value=ANNOTATIONS['value'],
            count=Count('value'),
        ).values(
            'value',
            'count'
        )
        perf_hvc = performance.annotate(
            is_hvc=ANNOTATIONS['is_hvc'],
            hvc_count=Coalesce(Count('is_hvc', filter=Q(is_hvc=True)), Value(0)),
            non_hvc_count=Coalesce(Count('is_hvc', filter=Q(is_hvc=False)), Value(0)),
            jobs_new=Coalesce(Sum('number_new_jobs'), Value(0)),
            jobs_safeguarded=Coalesce(Sum('number_safeguarded_jobs'), Value(0)),
            jobs_total=Coalesce(Sum(F('number_new_jobs') + F('number_safeguarded_jobs')), Value(0))
        ).values(
            'value',
            'count',
            'hvc_count',
            'non_hvc_count',
            'jobs_new',
            'jobs_safeguarded',
            'jobs_total'
        )
        perf_by_value = fill_in_missing_performance(group_by_key(list(perf_hvc), 'value', flatten=True))
        performance_dict = make_nested(perf_by_value)
        performance_dict = add_is_on_target(performance_dict)
        won_and_verify_dict = {
            "count": won_and_verify_count,
            **total_value,
            "jobs": jobs,
            "campaign": {
                "hvc": {
                    "count": campaign['hvc_count'],
                    "percent": percentage_formatted(campaign['hvc_count'], won_and_verify_count)
                },
                "non_hvc": {
                    "count": campaign['non_hvc_count'],
                    "percent": percentage_formatted(campaign['non_hvc_count'], won_and_verify_count)
                }
            },
            "performance": performance_dict,
            "stages": stage_breakdown
        }
        return won_and_verify_dict


class FDIBaseSectorTeamView(BaseFDIView):

    def initial(self, request, team_id, *args, **kwargs):
        self.team = self._get_team(team_id)
        if not self.team:
            return self._not_found(detail=f'team with id: {team_id} not found')
        super(FDIBaseSectorTeamView, self).initial(
            request, team_id, *args, **kwargs)

    def _get_team(self, team_id):
        """ Get SectorTeam object or False if invalid ID """
        try:
            return SectorTeam.objects.get(id=int(team_id))
        except SectorTeam.DoesNotExist:
            return False

    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        return qs.for_sector_team(self.team)

    def get_targets(self):
        return self.team.targets.filter(financial_year=self.fin_year)

    def get(self, request, *args, **kwargs):
        return super(FDIBaseSectorTeamView, self).get(request, *args, **kwargs)


class FDISectorTeamListView(BaseFDIView):

    def get(self, request, *args, **kwargs):
        all_sectors = SectorTeam.objects.all().order_by('id')
        formatted_sector_teams = [
            {
                'id': x.id,
                'name': x.name,
                'description': x.description,
            } for x in all_sectors
        ]
        return self._success(formatted_sector_teams)


class FDIOverview(BaseFDIView):

    def get_results(self):
        return self._get_fdi_summary()


class FDISectorTeamDetailView(FDIBaseSectorTeamView):
    team = None

    def _group_investments(self, investments, condition):
        group_iter = itertools.groupby(investments, key=condition)
        groups = defaultdict(list)
        for stage, wins in group_iter:
            groups[stage] = list(wins)
        return groups

    def _item_breakdown(self, investments: List[Investments], target_num: int, target_objs=None):

        hvc_data = {}
        if target_objs:

            hvc_targets = set(target_objs.filter(
                hvc_target__gte=0).values_list('market', flat=True))

            def check_is_hvc(investment: Investments):
                market = investment.company_country_id
                return market in hvc_targets

            hvc_data['hvc_count'] = len(
                [x for x in investments if check_is_hvc(x)])

        grouped = self._group_investments(investments, classify_quality)
        data = {
            'total': len(investments),
            'progress': two_digit_float(len(investments) * 100 / target_num) if target_num else 0.0,
            'high': len(grouped['high']),
            'good': len(grouped['good']),
            'standard': len(grouped['standard']),
            'value': sum([x.investment_value for x in investments]),
            **hvc_data
        }

        return data

    def _get_market_target(self, market):
        target = 0
        try:
            target_obj = MarketTarget.objects.get(
                sector_team=self.team, market=market)

            if target_obj.target:
                target += target_obj.target
        except MarketTarget.DoesNotExist:
            return 0

        return target

    def _get_sector_team_target(self, market):
        target = 0
        try:
            target_obj = SectorTeamTarget.objects.get(
                sector_team=self.team, market=market)
            if target_obj.target:
                target += target_obj.target
        except SectorTeamTarget.DoesNotExist:
            return 0

        return target

    def _market_breakdown(self, investments, market):
        # order investments by stage and then by quality so as to group them easily
        market_investments = investments.filter(
            company_country__in=market.countries.all()).order_by(
                'stage', 'fdi_value__name')
        grouped = self._group_investments(market_investments, classify_stage)

        target = self._get_market_target(market)

        # TODO target distribution needs a home in database, not here
        target_data = {
            'total': target,
            'progress': 100.0,
            'high': target * 40 / 100,
            'good': target * 30 / 100,
            'standard': target * 30 / 100,
        }

        market_data = {
            "id": market.id,
            "name": market.name,
            "verified": self._item_breakdown(grouped['verfied'], target),
            "confirmed": self._item_breakdown(grouped['confirmed'], target),
            "pipeline": self._item_breakdown(grouped['pipeline'], 0),
            "target": target_data,
        }
        return market_data

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = {}
        results['name'] = self.team.name
        results['description'] = self.team.description
        results['overview'] = self._get_fdi_summary()

        markets = Market.objects.all()
        market_data = [self._market_breakdown(
            investments_in_scope, market) for market in markets]

        results['markets'] = market_data
        return self._success(results)


class FDISectorTeamHVCDetailView(FDISectorTeamDetailView):
    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        qs = qs.for_sector_team(self.team)
        hvc_markets = [t.market for t in SectorTeamTarget.objects.filter(
            target__isnull=False, sector_team=self.team.id)]
        hvc_countries = Country.objects.filter(market__in=hvc_markets)
        return qs.filter(company_country__in=hvc_countries)

    def _get_sector_team_target(self, market):
        target = 0
        try:
            target_obj = SectorTeamTarget.objects.get(
                sector_team=self.team, market=market)
            if target_obj.target:
                target += target_obj.target
        except SectorTeamTarget.DoesNotExist:
            return 0

        return target

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = {}
        results['name'] = self.team.name
        results['description'] = self.team.description
        results['overview'] = self._get_fdi_summary()

        hvc_markets = [t.market for t in SectorTeamTarget.objects.filter(
            target__isnull=False, sector_team=self.team.id)]
        market_data = [self._market_breakdown(
            investments_in_scope, market) for market in hvc_markets]

        results['markets'] = market_data
        return self._success(results)


class FDISectorTeamNonHVCDetailView(FDISectorTeamDetailView):
    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        qs = qs.for_sector_team(self.team)
        non_hvc_markets = [t.market for t in MarketTarget.objects.filter(
            target__isnull=False, sector_team=self.team.id)]
        non_hvc_countries = Country.objects.filter(market__in=non_hvc_markets)
        return qs.filter(company_country__in=non_hvc_countries)

    def _get_market_target(self, market):
        target = 0
        try:
            target_obj = MarketTarget.objects.get(
                sector_team=self.team, market=market)
            if target_obj.target:
                target += target_obj.target
        except MarketTarget.DoesNotExist:
            return 0

        return target

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = {}
        results['name'] = self.team.name
        results['description'] = self.team.description
        results['overview'] = self._get_fdi_summary()

        non_hvc_markets = [t.market for t in MarketTarget.objects.filter(
            target__isnull=False, sector_team=self.team.id)]
        market_data = [self._market_breakdown(
            investments_in_scope, market) for market in non_hvc_markets]

        results['markets'] = market_data
        return self._success(results)


class FDISectorTeamOverview(FDISectorTeamDetailView):

    def initial(self, request, team_id, *args, **kwargs):
        super(FDIBaseSectorTeamView, self).initial(
            request, team_id, *args, **kwargs)

    def _get_team(self, team_id):
        """ Get SectorTeam object or False if invalid ID """
        return False

    def get_queryset(self):
        qs = super(FDIBaseSectorTeamView, self).get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        return qs

    def _get_sector_target(self, sector_team):
        target = 0
        target_objs = SectorTeamTarget.objects.filter(
            sector_team=sector_team, financial_year=self.fin_year)
        # both HVC and non-HVC targets
        for t in target_objs:
            if t.target:
                target += t.target
        return target, target_objs

    def _sector_team_breakdown(self, investments, sector_team: SectorTeam):

        # order investments by stage and then by quality so as to group them easily
        sector_team_investments = investments.filter(
            sector__in=sector_team.sectors.all()).order_by(
            'stage', 'fdi_value__name')
        grouped = self._group_investments(
            sector_team_investments, classify_stage)

        target, target_objs = self._get_sector_target(sector_team)

        # TODO target distribution needs a home in database, not here
        target_data = {
            'total': target,
            'progress': 100.0,
            'high': target * 40 / 100,
            'good': target * 30 / 100,
            'standard': target * 30 / 100,
        }

        sector_team_data = {
            "id": sector_team.id,
            "name": sector_team.name,
            "description": sector_team.description,
            "verified": self._item_breakdown(grouped['verfied'], target, target_objs),
            "confirmed": self._item_breakdown(grouped['confirmed'], target, target_objs),
            "pipeline": self._item_breakdown(grouped['pipeline'], 0, target_objs),
            "target": target_data,
        }
        return sector_team_data

    def get(self, request, *args, **kwargs):
        investments_in_scope = self.get_queryset()

        results = {}
        results['name'] = 'ALL'
        results['description'] = 'All'
        results['overview'] = self._get_fdi_summary()

        sector_teams = SectorTeam.objects.all()
        sector_teams_data = [self._sector_team_breakdown(
            investments_in_scope, sector_team) for sector_team in sector_teams]

        results['sector_teams'] = sector_teams_data
        return self._success(results)


class FDIYearOnYearComparison(BaseFDIView):

    def _fill_date_ranges(self):
        self.date_range = {
            "start": None,
            "end": self._date_range_end(),
        }

    def raw_queryset_as_values_list(self, raw_qs):
        columns = raw_qs.columns
        for row in raw_qs:
            yield {col: getattr(row, col) for col in columns}

    def get_results(self):
        projects_by_fy = """SELECT 
            get_financial_year(date_won) AS year,
            CASE
                WHEN fdi_value_id = '002c18d9-f5c7-4f3c-b061-aee09fce8416' THEN 'good'
                WHEN fdi_value_id = '38e36c77-61ad-4186-a7a8-ac6a1a1104c6' THEN 'high'
                WHEN fdi_value_id = '2bacde8d-128f-4d0a-849b-645ceafe4cf9' THEN 'standard'
                ELSE 'unknown' END
            AS value,
            COUNT(get_financial_year(date_won)) AS year__count,
            COUNT(
                CASE
                WHEN fdi_value_id = '002c18d9-f5c7-4f3c-b061-aee09fce8416' THEN 'good'
                WHEN fdi_value_id = '38e36c77-61ad-4186-a7a8-ac6a1a1104c6' THEN 'high'
                WHEN fdi_value_id = '2bacde8d-128f-4d0a-849b-645ceafe4cf9' THEN 'standard'
                ELSE 'unknown' END
            ) AS value__count,
            SUM(number_new_jobs) AS number_new_jobs__sum,
            SUM(number_safeguarded_jobs) AS number_safeguarded_jobs__sum,
            SUM(investment_value) AS investment_value__sum
        FROM fdi_investments
        WHERE (stage = 'won' AND date_won < %s AND date_won >= '2014-04-01')
        GROUP BY
            get_financial_year(date_won),
            CASE
                WHEN fdi_value_id = '002c18d9-f5c7-4f3c-b061-aee09fce8416' THEN 'good'
                WHEN fdi_value_id = '38e36c77-61ad-4186-a7a8-ac6a1a1104c6' THEN 'high'
                WHEN fdi_value_id = '2bacde8d-128f-4d0a-849b-645ceafe4cf9' THEN 'standard'
                ELSE 'unknown'
            END
        ORDER BY year ASC"""

        breakdown = []
        args = [self._date_range_end()]
        with connection.cursor() as cursor:
            cursor.execute(projects_by_fy, args)
            columns = [x.name for x in cursor.description]
            breakdown = [dict(zip(columns, row)) for row in cursor.fetchall()]

        year_buckets = sorted(list({x['year'] for x in breakdown}))
        results = [
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
        for year in results:
            for k in ['high', 'good', 'standard']:
                if not year.get(k):
                    year[k] = {
                        "count": 0,
                        "number_new_jobs__sum": 0,
                        "number_safeguarded_jobs__sum": 0,
                        "investment_value__sum": 0,
                    }
        return results


class FDISectorTeamWinTable(FDIBaseSectorTeamView):
    def get_hvc_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        qs = qs.for_sector_team(self.team)
        hvc_markets = [t.market for t in SectorTeamTarget.objects.filter(
            target__isnull=False, sector_team=self.team.id)]
        hvc_countries = Country.objects.filter(market__in=hvc_markets)
        return qs.filter(company_country__in=hvc_countries)

    def get_non_hvc_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        qs = qs.for_sector_team(self.team)
        non_hvc_markets = [t.market for t in MarketTarget.objects.filter(
            target__isnull=False, sector_team=self.team.id)]
        non_hvc_countries = Country.objects.filter(market__in=non_hvc_markets)
        return qs.filter(company_country__in=non_hvc_countries)

    def get_results(self):
        hvc_target = self.get_targets().aggregate(
            target=Coalesce(Sum('hvc_target'), 0))['target']
        non_hvc_target = self.get_targets().aggregate(
            target=Coalesce(Sum('non_hvc_target'), 0))['target']
        hvc_investments = InvestmentsSerializer(
            self.get_hvc_queryset().annotate(**ANNOTATIONS), many=True)
        non_hvc_investments = InvestmentsSerializer(
            self.get_non_hvc_queryset().annotate(**ANNOTATIONS), many=True)

        return {
            "name": self.team.name,
            "description": self.team.description,
            "target": {
                "hvc": hvc_target,
                "non_hvc": non_hvc_target,
                "total": sum([hvc_target, non_hvc_target])
            },
            "investments": {
                'hvc': hvc_investments.data,
                'non_hvc': non_hvc_investments.data
            }
        }
