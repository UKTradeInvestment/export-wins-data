from functools import reduce
from operator import or_
from typing import NamedTuple

from collections import defaultdict, namedtuple
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.text import slugify

from mi.utils import sort_campaigns_by
from mi.views.base_view import BaseWinMIView
from wins.constants import TEAMS, HQ_TEAM_REGION_OR_POST
from wins.models import HVC


class FakeTarget(NamedTuple):
    campaign_id: str
    name: str
    target: int = 0


class BaseTeamTypeMIView(BaseWinMIView):
    """ Abstract Base for other Team Type-related MI endpoints to inherit from """
    team_type = None

    @classmethod
    def as_view(cls, **initkwargs):
        # ensure team type is correct and crash early if not
        if initkwargs['team_type'] not in dict(TEAMS):
            raise ValueError('team_type is not valid')
        return super().as_view(**initkwargs)

    @cached_property
    def valid_options(self):
        return [
            {
                "slug": slugify(k.lstrip(self.team_type)),
                "id": k,
                "name": v
            }
            for k, v in HQ_TEAM_REGION_OR_POST if k.startswith(self.team_type)
        ]

    @cached_property
    def team(self):
        return [x for x in self.valid_options if x['slug'] == self.team_slug][0]

    @cached_property
    def team_type_key(self):
        """
        What to use in the result for the heading of the json response.
        Most of the time returning team_type is fine but override this if the
        database key for team type doesn't make sense
        """
        return self.team_type

    @cached_property
    def confirmation_time_filter(self):
        return {
            'win__hq_team': self.team['id'],
            'win__confirmation__created__range': (self._date_range_start(), self._date_range_end())
        }

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.handle_team_slug(kwargs)

    def handle_team_slug(self, kwargs):
        # ensure team_id is in team_type
        self.team_slug = kwargs.get('team_slug')
        if self.team_slug not in [x['slug'] for x in self.valid_options]:
            self._not_found(f'{self.team_slug} is not a valid {self.team_type_key}')

    @property
    def _team_type_result(self):
        return {
            "id": self.team['slug'],
            "name": self.team['name'],
            "avg_time_to_confirm": self._average_confirm_time(**self.confirmation_time_filter),
        }

    @cached_property
    def _team_filter(self):
        return Q(team_type=self.team_type) & Q(hq_team=self.team['id'])

    def _wins_filter(self):
        wf = super()._wins_filter()
        return wf & self._team_filter

    def _get_all_wins(self):
        return self._hvc_wins() | self._non_hvc_wins()

    def _result(self):
        raise NotImplementedError('subclass must implement ._result')

    def get(self, request, *args, **kwargs):
        return self._success(self._result())

    def wins_to_campaigns(self, wins_qs):

        def only_unique(campaigns):
            seen = set()
            ret = []
            for campaign in campaigns:
                campaign_id = campaign['campaign_id']
                if campaign_id not in seen:
                    seen.add(campaign_id)
                    ret.append(campaign)
            return ret

        hvc_set = {w['hvc'] for w in wins_qs if w['hvc']}
        if not hvc_set:
            return []
        hvc_filter = reduce(or_, [Q(**{'campaign_id': hvc[:4], 'financial_year': hvc[-2:]}) for hvc in hvc_set])
        return only_unique(
            HVC.objects.filter(hvc_filter).values(
                'campaign_id', 'name'
            ).order_by(
                '-financial_year', 'name'
            )
        )


class TeamTypeListView(BaseTeamTypeMIView):

    def get(self, request, *args, **kwargs):
        return self._success([{'id': x['slug'], 'name': x['name']} for x in self.valid_options])

    def handle_team_slug(self, kwargs):
        """
        The base url doesn't have a <team_slug> so we don't need to handle it
        """
        pass


class TeamTypeDetailView(BaseTeamTypeMIView):

    def _result(self):
        """
        Formatted result for a post
        """
        return {
            **self._team_type_result,
            "avg_time_to_confirm": self._average_confirm_time(**self.confirmation_time_filter),
            "wins": self._breakdowns(self._hvc_wins(), non_hvc_wins=self._non_hvc_wins(), include_non_hvc=True),
        }


class TeamTypeWinTableView(BaseTeamTypeMIView):

    def _result(self):
        return {
            self.team_type_key: {
                "id": self.team['slug'],
                "name": self.team['name'],
            },
            "avg_time_to_confirm": self._average_confirm_time(**self.confirmation_time_filter),
            "wins": self._win_table_wins(self._hvc_wins(), self._non_hvc_wins())
        }


class TeamTypeNonHvcWinsView(BaseTeamTypeMIView):

    def _result(self):
        return self._top_non_hvc(self._non_hvc_wins())


class TeamTypeMonthsView(BaseTeamTypeMIView):

    def _result(self):
        wins = self._get_all_wins()
        hvcs = self.wins_to_campaigns(wins)
        return {
            **self._team_type_result,
            "avg_time_to_confirm": self._average_confirm_time(**self.confirmation_time_filter),
            "hvcs": {
                "target": 0,
                "campaigns": {x['name'] for x in hvcs}
            },
            'months': self._month_breakdowns(wins, include_non_hvc=True)
        }


class TeamTypeCampaignsView(BaseTeamTypeMIView):

    """ Team HVC's view along with their win-breakdown """

    @cached_property
    def confirmation_time_filter(self):
        """
        This overrides the base filter for avg_time_to_confirm
        because this is a hvc only view so it should make sure
        that the average only considers HVCs
        """
        return {
            **super().confirmation_time_filter,
            'win__hvc__isnull': False,
            'win__hvc__gt': ''
        }

    def _group_wins_by_target(self, wins, targets=None):
        if targets:
            return super()._group_wins_by_target(wins, targets)

        campaigns = self.wins_to_campaigns(wins)

        # ignore real targets (which are for country/sector) and set 0
        # for target as it is the only thing that makes sense for a
        # post

        synthetic_targets = [
            FakeTarget(
                campaign['campaign_id'],
                campaign['name']
            ) for campaign in campaigns
        ]

        return super()._group_wins_by_target(wins, synthetic_targets)

    def _campaign_breakdowns(self):
        wins = self._hvc_wins()
        campaign_to_wins = self._group_wins_by_target(wins)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, 0),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]
        sorted_campaigns = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        return sorted_campaigns

    def _result(self):
        breakdown = self._campaign_breakdowns()
        return {
            **self._team_type_result,
            "hvcs": {
                "campaigns": [f'{x["campaign"]}: {x["campaign_id"]}' for x in breakdown],
                "target": 0
            },
            "campaigns": breakdown,

        }
