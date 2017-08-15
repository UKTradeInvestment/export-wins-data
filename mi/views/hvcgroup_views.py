from itertools import groupby
from operator import attrgetter, itemgetter

from mi.models import HVCGroup
from mi.utils import month_iterator
from mi.views.sector_views import BaseSectorMIView


class BaseHVCGroupMIView(BaseSectorMIView):
    """ Abstract Base for other HVC Group MI endpoints to inherit from """

    def _get_hvc_group(self, group_id):
        try:
            return HVCGroup.objects.get(id=int(group_id))
        except HVCGroup.DoesNotExist:
            return False

    def _group_result(self, group):
        """ Basic data about HVC Group - name & hvc's """
        return {
            'name': group.name,
            'avg_time_to_confirm': self._average_confirm_time_for_wins(self._get_group_wins(group)),
            'hvcs': self._hvc_overview(group.fin_year_targets(fin_year=self.fin_year)),
        }


class HVCGroupsListView(BaseHVCGroupMIView):
    def get(self, request):
        results = [
            {
                'id': hvc_group.id,
                'name': hvc_group.name,
            }
            for hvc_group in self._hvc_groups_for_fin_year()
        ]
        return self._success(sorted(results, key=itemgetter('name')))


class HVCGroupDetailView(BaseHVCGroupMIView):
    """ HVC Group details with name, targets and win-breakdown """

    def get(self, request, group_id):
        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        wins = self._get_group_wins(group)
        results['wins'] = self._breakdowns(wins, include_non_hvc=False)
        return self._success(results)


class HVCGroupMonthsView(BaseHVCGroupMIView):
    """
    This view provides cumulative totals for all wins for a given HVC Group,
    grouped by month, for current financial year
    """

    def get(self, request, group_id):

        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        wins = self._get_group_wins(group)
        results['months'] = self._month_breakdowns(wins, include_non_hvc=False)
        return self._success(results)


class HVCGroupCampaignsView(BaseHVCGroupMIView):
    """ All campaigns for a given HVC Group and their win-breakdown"""

    def _campaign_breakdowns(self, group):
        wins = self._get_group_wins(group)
        group_targets = group.fin_year_targets(fin_year=self.fin_year)
        campaign_to_wins = self._group_wins_by_target(wins, group_targets)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]
        sorted_campaigns = sorted(
            campaigns,
            key=lambda c: (
                c['totals']['progress']['confirmed_percent'],
                c['totals']['progress']['unconfirmed_percent'],
                c['totals']['target']
            ),
            reverse=True,
        )
        return sorted_campaigns

    def get(self, request, group_id):
        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        results['campaigns'] = self._campaign_breakdowns(group)
        return self._success(results)


class HVCGroupWinTableView(BaseHVCGroupMIView):
    def get(self, request, group_id):
        group = self._get_hvc_group(group_id)
        if not group:
            return self._not_found()

        wins = self._get_group_wins(group)
        results = {
            "hvc_group": {
                "id": group_id,
                "name": group.name,
            },
            "wins": self._win_table_wins(wins)
        }
        return self._success(results)
