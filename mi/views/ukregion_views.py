import itertools
from operator import itemgetter

from collections import defaultdict
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.text import slugify

from core.utils import filter_key
from mi.models import UKRegionTarget
from mi.views.team_type_views import TeamTypeListView, TeamTypeDetailView, TeamTypeWinTableView, \
    TeamTypeNonHvcWinsView, TeamTypeMonthsView, TeamTypeCampaignsView
from mi.utils import percentage_formatted
from wins.constants import UK_REGIONS_MAP, UK_REGIONS, STATUS as EXPORT_EXPERIENCE, UK_SUPER_REGIONS
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

    @property
    def _team_filter(self):
        all_teams = FLATTENED_REGIONS[self.team['id']]
        return Q(hq_team__in=all_teams)

    @property
    def _advisor_filter(self):
        """ UK Region specific filter for contributing wins """
        all_teams = FLATTENED_REGIONS[self.team['id']]
        return Q(advisors__hq_team__in=all_teams)


class UKRegionTeamTypeNameMixin:
    """
    This changes the key in the results set to be 'uk_regions' instead of
    the database id for this team type

    Mixin that should be used with a subclass of `BaseTeamTypeMIView`
    """

    @property
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
        all_uk_regions = itertools.chain.from_iterable(
            x.keys() for x in UK_REGIONS_MAP.values())

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

        group_iter = itertools.groupby(self._non_hvc_wins().order_by(
            'export_experience'), key=classify_experience)
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

    @property
    def target(self):
        try:
            target = UKRegionTarget.objects.get(
                financial_year=self.fin_year, region=self.team['id']).as_dict()
        except UKRegionTarget.DoesNotExist:
            target = {'target': None}
        return target


def get_region_group_by_region_id(region_id):
    lookup = {}
    for super_region_id, region_ids in UK_REGIONS_MAP.items():
        for lookup_region_id in region_ids:
            lookup[lookup_region_id] = super_region_id
    return lookup[region_id]


def group_by_superregion(regions):
    regions.sort(key=itemgetter('super_region'))
    groups = defaultdict(list)
    for group, vals in itertools.groupby(regions, key=itemgetter('super_region')):
        groups[group] = [filter_key(region_data, 'super_region') for region_data in vals]
    return [
        {
            "name": UK_SUPER_REGIONS.values[k].display,
            "regions": v
        } for k, v in groups.items()
    ]


def is_devolved(super_region):
    sr = UK_SUPER_REGIONS.for_display(super_region).value
    return sr == UK_SUPER_REGIONS.DEVOLVED


class UKRegionListView(UKRegionMixin, TeamTypeListView):

    def get(self, request, *args, **kwargs):
        regions = []
        for x in self.valid_options:
            super_region = get_region_group_by_region_id(x['id'])
            regions.append({
                'id': x['slug'],
                'name': x['name'],
                'super_region': super_region
            })
        grouped_regions = group_by_superregion(regions)
        grouped_regions = [
            {
                **super_region,
                'devolved': is_devolved(super_region['name'])}
            for super_region in grouped_regions
        ]
        return self._success(
            {'region_groups': grouped_regions}
        )


class UKRegionOverview(UKRegionMixin, TeamTypeListView):

    def wins_non_hvc_performance(self, wins, target):
        wins_performance = {
            'target': target,
            'performance': {
                'confirmed': percentage_formatted(wins['export']['non_hvc']['number']['confirmed'], target),
                'unconfirmed': percentage_formatted(wins['export']['non_hvc']['number']['unconfirmed'], target)
            }
        }
        return wins_performance

    def export_experience_performance(self, confirmed, unconfirmed, target):
        performance = {
            'target': target,
            'percentage': {
                'confirmed': percentage_formatted(confirmed, target),
                'unconfirmed': percentage_formatted(unconfirmed, target)
            }
        }
        return performance

    def summary_of_regions(self, regions):
        non_hvcs = [n['wins']['export']['non_hvc'] for n in regions]
        conf_number = sum(non_hvc['number']['confirmed']
                          for non_hvc in non_hvcs)
        unconf_number = sum(non_hvc['number']['unconfirmed']
                            for non_hvc in non_hvcs)
        target = sum(non_hvc['performance']['target'] for non_hvc in non_hvcs)
        summary = {
            "non_hvc": {
                "value": {
                    "confirmed": sum(non_hvc['value']['confirmed'] for non_hvc in non_hvcs),
                    "unconfirmed": sum(non_hvc['value']['unconfirmed'] for non_hvc in non_hvcs),
                    "total": sum(non_hvc['value']['total'] for non_hvc in non_hvcs)
                },
                "number": {
                    "confirmed": conf_number,
                    "unconfirmed": unconf_number,
                    "total": sum(non_hvc['number']['total'] for non_hvc in non_hvcs)
                },
                "performance": {
                    "target": sum(non_hvc['performance']['target'] for non_hvc in non_hvcs),
                    "percentage": {
                        'confirmed': percentage_formatted(conf_number, target),
                        'unconfirmed': percentage_formatted(unconf_number, target),
                    }
                }
            }
        }
        return summary

    def get(self, request, *args, **kwargs):
        regions = []
        region_targets = UKRegionTarget.objects.filter(
            financial_year=self.fin_year)

        for x in self.valid_options:
            try:
                target = region_targets.get(region=x['id']).as_dict()

                self.team_slug = x['slug']

                wins = self._breakdowns(
                    include_hvc=False, non_hvc_wins=self._non_hvc_wins())
                wins_perf = self.wins_non_hvc_performance(
                    wins, target['target']['total'])
                wins['export']['non_hvc']['performance'] = wins_perf

                export_experience = self.breakdown_by_experience()
                for key, experience in export_experience.items():
                    if key != 'unknown':
                        exp_performance = self.export_experience_performance(experience['number']['confirmed'],
                                                                             experience['number']['unconfirmed'],
                                                                             target['target'][key])
                        experience['performance'] = exp_performance

                region_result = {
                    'id': x['slug'],
                    'name': x['name'],
                    **target,
                    'wins': wins,
                    'export_experience': export_experience,
                    'super_region': get_region_group_by_region_id(x['id'])
                }
                regions.append(region_result)
            except UKRegionTarget.DoesNotExist:
                pass

        result = {
            'summary': self.summary_of_regions(regions),
            "region_groups": group_by_superregion(regions),
        }
        return self._success(result)


class UKRegionDetailView(UKRegionMixin, TeamTypeDetailView):

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
                **self.target
            },
            'months': self._month_breakdowns(wins, include_non_hvc=True),
        }


class UKRegionCampaignsView(UKRegionMixin, TeamTypeCampaignsView):
    pass
