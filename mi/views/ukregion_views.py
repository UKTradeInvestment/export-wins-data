import itertools

from collections import defaultdict
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.text import slugify

from mi.models import UKRegionTarget
from mi.views.team_type_views import TeamTypeListView, TeamTypeDetailView, TeamTypeWinTableView, \
    TeamTypeNonHvcWinsView, TeamTypeMonthsView, TeamTypeCampaignsView
from wins.constants import UK_REGIONS_MAP, UK_REGIONS, STATUS as EXPORT_EXPERIENCE
from wins.models import Win

FLATTENED_REGIONS = {}
for v in UK_REGIONS_MAP.values():
    FLATTENED_REGIONS = {**FLATTENED_REGIONS, **v}


class UKRegionWinsFilterMixin:
    """
    Changes TeamType view's wins query a set of teams instead of just one.
    Mixin that must be used with a subclass of `BaseTeamTypeMIView`
    """

    @cached_property
    def confirmation_time_filter(self):
        all_teams = FLATTENED_REGIONS[self.team['id']]
        return {
            'win__hq_team__in': all_teams,
            'win__confirmation__created__range': (self._date_range_start(), self._date_range_end())
        }

    @cached_property
    def _team_filter(self):
        all_teams = FLATTENED_REGIONS[self.team['id']]
        return Q(hq_team__in=all_teams)


class UKRegionTeamTypeNameMixin:
    """
    This changes the key in the results set to be 'uk_regions' instead of
    the database id for this team type

    Mixin that should be used with a subclass of `BaseTeamTypeMIView`
    """

    @cached_property
    def team_type_key(self):
        """
        What to use in the result for the heading of the json response.
        Most of the time returning team_type is fine but override this if the
        database key for team type doesn't make sense
        """
        return 'uk_region'


class UKRegionValidOptionsMixin:
    """
    This affects both the list view and the parameters passed via slug to
    return uk regions instead of individual teams, and to accept the slugified
    version of the uk_region name
    Mixin that should be used with a subclass of `BaseTeamTypeMIView`
    """

    @cached_property
    def valid_options(self):
        all_uk_regions = itertools.chain.from_iterable(x.keys() for x in UK_REGIONS_MAP.values())

        return [
            {
                "slug": slugify(UK_REGIONS.for_value(uk_region_id)[-1]),
                "id": uk_region_id,
                "name": UK_REGIONS.for_value(uk_region_id)[-1]
            }
            for uk_region_id in all_uk_regions
        ]


class UKRegionMixin(
    UKRegionWinsFilterMixin,
    UKRegionValidOptionsMixin,
    UKRegionTeamTypeNameMixin
):
    @property
    def target(self):
        try:
            target = UKRegionTarget.objects.get(financial_year=self.fin_year, region=self.team['id']).as_dict()
        except UKRegionTarget.DoesNotExist:
            target = {'target': None}
        return target


class UKRegionListView(UKRegionMixin, TeamTypeListView):
    pass


class UKRegionOverview(UKRegionMixin, TeamTypeListView):

    def get(self, request, *args, **kwargs):
        regions = []
        region_targets = UKRegionTarget.objects.filter(financial_year=self.fin_year)
        for x in self.valid_options:
            try:
                target = region_targets.get(region=x['id']).as_dict()
            except UKRegionTarget.DoesNotExist:
                target = {'target': None}

            regions.append({'id': x['slug'], 'name': x['name'], **target})
        return self._success(regions)


class UKRegionDetailView(UKRegionMixin, TeamTypeDetailView):

    def _group_wins_by_export_experience(self):

        def classify_experience(win):
            exp_id = win['export_experience']
            if exp_id in EXPORT_EXPERIENCE.new_exporter:
                return 'new_exporters'
            elif exp_id in EXPORT_EXPERIENCE.sustainable:
                return 'sustainable'
            elif exp_id in EXPORT_EXPERIENCE.growth:
                return 'growth'
            else:
                return 'unknown'

        group_iter = itertools.groupby(self._get_all_wins().order_by('export_experience'), key=classify_experience)
        groups = defaultdict(list)
        for export_exp, wins in group_iter:
            groups[export_exp] = list(wins)
        return groups

    def breakdown_by_experience(self):
        """
        Result looks like:
        {
            'new_exporter': {
                'value': ...,
                'number': ...,
            },
            'sustainable': {
                'value': ...,
                'number': ...,
            }
            'growth': {
                'value': ...,
                'number': ...,
            }
        }
        """

        grouped_wins = self._group_wins_by_export_experience()
        data = {
            exp: self._breakdown_wins(wins) for exp, wins in grouped_wins.items()
        }
        data.update({'total': self._breakdown_wins(self._wins())})
        return data

    def _result(self):
        result = super()._result()
        return {
            **result,
            'export_experience': self.breakdown_by_experience(),
            **self.target
        }


class UKRegionWinTableView(UKRegionMixin, TeamTypeWinTableView):
    pass


class UKRegionNonHvcWinsView(UKRegionMixin, TeamTypeNonHvcWinsView):
    pass


class UKRegionMonthsView(UKRegionMixin, TeamTypeMonthsView):

    def _result(self):
        wins = self._get_all_wins()
        return {
            **self._team_type_result,
            "avg_time_to_confirm": self._average_confirm_time(**self.confirmation_time_filter),
            'export_experience': {
                'target': self.target
            },
            'months': self._month_breakdowns(wins, include_non_hvc=True),
        }


class UKRegionCampaignsView(UKRegionMixin, TeamTypeCampaignsView):
    pass
