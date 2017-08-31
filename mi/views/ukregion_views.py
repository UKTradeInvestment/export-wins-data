import itertools

from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.text import slugify

from mi.views.team_type_views import TeamTypeListView, TeamTypeDetailView, TeamTypeWinTableView, \
    TeamTypeNonHvcWinsView, TeamTypeMonthsView, TeamTypeCampaignsView
from wins.constants import UK_REGIONS_MAP, UK_REGIONS

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
    pass


class UKRegionListView(UKRegionMixin, TeamTypeListView):
    pass


class UKRegionDetailView(UKRegionMixin, TeamTypeDetailView):
    pass


class UKRegionWinTableView(UKRegionMixin, TeamTypeWinTableView):
    pass


class UKRegionNonHvcWinsView(UKRegionMixin, TeamTypeNonHvcWinsView):
    pass


class UKRegionMonthsView(UKRegionMixin, TeamTypeMonthsView):
    pass


class UKRegionCampaignsView(UKRegionMixin, TeamTypeCampaignsView):
    pass
