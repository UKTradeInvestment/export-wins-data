import itertools
from typing import List

from collections import defaultdict

from django.db.models import Func, F, Q, Sum, When, Case, Value, CharField, Count, BooleanField
from django.db.models.functions import Coalesce
from django.db import connection
import django_filters.rest_framework as filters

from core.utils import group_by_key, getitem_or_default
from fdi.models import (
    Country,
    Investments,
    Market,
    MarketTarget,
    OverseasRegion,
    OverseasRegionMarket,
    SectorTeam,
    SectorTeamTarget,
    UKRegion
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
        When(hvc_code__isnull=False, then=Value(
            True, output_field=BooleanField())),
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
        {'count': 0, 'percent': 0.0},
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


def investments_breakdown_by_sector_team(qs):
    other_sector = SectorTeam.objects.get(name='Other')

    stage_data = qs.values(
        'sector__sectorteamsector__team__id',
        'stage'
    ).annotate(
        count=Count('id'),
    ).values(
        'sector__sectorteamsector__team__id',
        'stage', 'count'
    )
    # there are some investments with no sector specified, push them to 'Other' team
    for stage_dict in list(stage_data):
        stage_dict.update((k, other_sector.id)
                          for k, v in stage_dict.items() if v is None)

    hvc_data = qs.values(
        'sector__sectorteamsector__team__id',
        'hvc_code'
    ).annotate(
        count=Count('id'),
    ).values(
        'sector__sectorteamsector__team__id',
        'hvc_code', 'count'
    )
    # there are some investments with no sector specified, push them to 'Other' team
    for hvc_dict in list(hvc_data):
        hvc_dict.update((k, other_sector.id)
                        for k, v in hvc_dict.items() if v is None)

    return list(stage_data), list(hvc_data)


def investments_breakdown_by_overseas(qs):
    stage_data = qs.values(
        'company_country__market__overseasregion__id',
        'stage'
    ).annotate(
        count=Count('id'),
    ).values(
        'company_country__market__overseasregion__id',
        'stage', 'count'
    )

    hvc_data = qs.values(
        'company_country__market__overseasregion__id',
        'hvc_code'
    ).annotate(
        count=Count('id'),
    ).values(
        'company_country__market__overseasregion__id',
        'hvc_code', 'count'
    )

    return list(stage_data), list(hvc_data)


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

    quality = filters.CharFilter(
        field_name='fdi_value__name', lookup_expr='iexact')
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
            total_investment_value__sum=Coalesce(
                Sum('investment_value'), Value(0))
        )
        jobs = won_and_verify.aggregate(
            new=Coalesce(Sum('number_new_jobs'), Value(0)),
            safeguarded=Coalesce(Sum('number_safeguarded_jobs'), Value(0)),
            total=Coalesce(Sum(F('number_new_jobs') +
                               F('number_safeguarded_jobs')), Value(0))
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

        # assert campaign_total == won_and_verify_count

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
            hvc_count=Coalesce(
                Count('is_hvc', filter=Q(is_hvc=True)), Value(0)),
            non_hvc_count=Coalesce(
                Count('is_hvc', filter=Q(is_hvc=False)), Value(0)),
            jobs_new=Coalesce(Sum('number_new_jobs'), Value(0)),
            jobs_safeguarded=Coalesce(
                Sum('number_safeguarded_jobs'), Value(0)),
            jobs_total=Coalesce(
                Sum(F('number_new_jobs') + F('number_safeguarded_jobs')), Value(0))
        ).values(
            'value',
            'count',
            'hvc_count',
            'non_hvc_count',
            'jobs_new',
            'jobs_safeguarded',
            'jobs_total'
        )
        perf_by_value = fill_in_missing_performance(
            group_by_key(list(perf_hvc), 'value', flatten=True))
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


class FDITabOverview(BaseFDIView):

    def _get_tab_queryset(self, name, tab_item):
        """
        """
        if name == "sector":
            assert isinstance(tab_item, SectorTeam)
            sector_team = tab_item
            return self.queryset.filter(sector__in=sector_team.sectors.all())
        elif name == "os_region":
            assert isinstance(tab_item, OverseasRegion)
            sector_team = tab_item
            return self.queryset.filter(sector__in=sector_team.sectors.all())
        elif name == "uk_region":
            assert isinstance(tab_item, UKRegion)
            sector_team = tab_item
            return self.queryset.filter(sector__in=sector_team.sectors.all())

    def _group_investments(self, investments, condition):
        group_iter = itertools.groupby(investments, key=condition)
        groups = defaultdict(list)
        for stage, wins in group_iter:
            groups[stage] = len(list(wins))
        return groups

    def _sector_team_breakdown(self, stage_investments, hvc_investments, sector_team: SectorTeam):

        stage_team = [
            i for i in stage_investments if i['sector__sectorteamsector__team__id'] == sector_team.id]
        hvc_team = [
            i for i in hvc_investments if i['sector__sectorteamsector__team__id'] == sector_team.id]
        confirmed = verified = pipeline = 0
        for i in stage_team:
            if i['stage'] == 'won':
                confirmed = i['count']
            elif i['stage'] == 'verify win':
                verified = i['count']
            elif i['stage'] == 'active':
                pipeline = i['count']

        hvc = 0
        for i in hvc_team:
            hvc = i['count']

        target = sector_team.fin_year_target(self.fin_year)

        sector_team_data = {
            "id": sector_team.id,
            "name": sector_team.description,
            "short_name": sector_team.name,
            "wins": {
                "verify_win": verified,
                "won": confirmed,
                "hvc_wins": hvc,
                "total": verified + confirmed,
            },
            "target": target,
            "pipeline": pipeline
        }
        return sector_team_data

    def _os_regions_breakdown(self, stage, quality, os_region: OverseasRegion):

        stage_region = [
            i for i in stage if i['company_country__market__overseasregion__id'] == os_region.id]
        hvc_region = [
            i for i in quality if i['company_country__market__overseasregion__id'] == os_region.id]
        confirmed = verified = pipeline = 0
        for i in stage_region:
            if i['stage'] == 'won':
                confirmed = i['count']
            elif i['stage'] == 'verify win':
                verified = i['count']
            elif i['stage'] == 'active':
                pipeline = i['count']

        hvc = 0
        for i in hvc_region:
            hvc = i['count']

        target = os_region.fin_year_target(self.fin_year)

        os_region_data = {
            "id": os_region.id,
            "name": os_region.name,
            "short_name": os_region.name,
            "wins": {
                "verify_win": verified,
                "won": confirmed,
                "hvc_wins": hvc,
                "total": verified + confirmed,
            },
            "target": target,
            "pipeline": pipeline
        }
        return os_region_data

    def get_results(self, name):
        investments_in_scope = self.filter_queryset(self.get_queryset())
        won_verify_and_active = investments_in_scope.won_verify_and_active()

        if name == "sector":
            stage, hvc = investments_breakdown_by_sector_team(
                won_verify_and_active)
            sector_teams = SectorTeam.objects.all()
            sector_teams_data = [self._sector_team_breakdown(
                stage, hvc, sector_team) for sector_team in sector_teams]
            return sector_teams_data
        elif name == "os_region":
            stage, hvc = investments_breakdown_by_overseas(
                won_verify_and_active)
            os_regions = OverseasRegion.objects.all()
            os_region_data = [self._os_regions_breakdown(
                stage, hvc, os_region) for os_region in os_regions]
            return os_region_data

    def get(self, request, name):
        valid_names = ['sector', 'os_region']
        if name not in valid_names:
            self._not_found()
        return self._success(self.get_results(name))
