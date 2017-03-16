from itertools import groupby
from operator import attrgetter

from mi.models import Target, HVCGroup
from mi.utils import (
    get_financial_start_date,
    month_iterator,
)
from mi.views.sector_views import BaseSectorMIView
from wins.models import Notification


class BaseHVCGroupMIView(BaseSectorMIView):
    """ Abstract Base for other HVC Group MI endpoints to inherit from """

    def _get_hvc_group(self, group_id):
        try:
            return HVCGroup.objects.get(id=int(group_id))
        except HVCGroup.DoesNotExist:
            return False

    def _get_avg_confirm_time(self, group):
        """
        Average of (earliest CUSTOMER notification created date - customer response date) for given team
        """
        group_targets = [s.campaign_id for s in group.targets.all()]
        notifications_qs = Notification.objects.filter(
            type__exact='c',
            win__hvc__in=group_targets,
            win__confirmation__isnull=False,
        )
        return self._average_confirm_time(notifications_qs)

    def _group_result(self, group):
        """ Basic data about HVC Group - name & hvc's """
        return {
            'name': group.name,
            'avg_time_to_confirm': self._get_avg_confirm_time(group),
            'hvcs': self._hvc_overview(group.targets.all()),
        }


class HVCGroupsListView(BaseHVCGroupMIView):
    def get(self, request):
        results = [
            {
                'id': hvc_group.id,
                'name': hvc_group.name,
            }
            for hvc_group in HVCGroup.objects.all()
            ]
        return self._success(results)


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

    def _month_breakdowns(self, wins):
        month_to_wins = self._group_wins_by_month(wins)
        return [
            {
                'date': date_str,
                'totals': self._breakdowns_cumulative(month_wins, include_non_hvc=False),
            }
            for date_str, month_wins in month_to_wins
            ]

    def _group_wins_by_month(self, wins):
        date_attrgetter = attrgetter('date')
        sorted_wins = sorted(wins, key=date_attrgetter)
        month_to_wins = []
        # group all wins by month-year
        for k, g in groupby(sorted_wins, key=date_attrgetter):
            month_wins = list(g)
            date_str = month_wins[0].date.strftime('%Y-%m')
            month_to_wins.append((date_str, month_wins))

        # Add missing months within the financial year until current month
        for item in month_iterator(get_financial_start_date()):
            date_str = '{:d}-{:02d}'.format(*item)
            existing = [m for m in month_to_wins if m[0] == date_str]
            if len(existing) == 0:
                # add missing month and an empty list
                month_to_wins.append((date_str, list()))

        return sorted(month_to_wins, key=lambda tup: tup[0])

    def get(self, request, group_id):

        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        wins = self._get_group_wins(group)
        results['months'] = self._month_breakdowns(wins)
        return self._success(results)


class HVCGroupCampaignsView(BaseHVCGroupMIView):
    """ All campaigns for a given HVC Group and their win-breakdown"""

    def _campaign_breakdowns(self, group):
        campaign_to_wins = self._group_wins_by_campaign(group)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
            ]
        sorted_campaigns = sorted(campaigns,
                                  key=lambda c: (
                                    c['totals']['progress']['confirmed_percent'],
                                    c['totals']['progress']['unconfirmed_percent'],
                                    c['totals']['target']),
                                  reverse=True)
        return sorted_campaigns

    def _group_wins_by_campaign(self, group):
        wins = self._get_group_wins(group)
        group_targets = group.targets.all()
        hvc_attrgetter = attrgetter('hvc')
        sorted_wins = sorted(wins, key=hvc_attrgetter)
        campaign_to_wins = []

        # group existing wins by campaign
        for k, g in groupby(sorted_wins, key=hvc_attrgetter):
            campaign_wins = list(g)
            campaign_to_wins.append((Target.objects.get(campaign_id=k), campaign_wins))

        # add remaining campaigns
        for target in group_targets:
            target_campaign = Target.objects.get(campaign_id=target.campaign_id)
            if not any(target_campaign in campaign_to_win for campaign_to_win in campaign_to_wins):
                campaign_to_wins.append((target_campaign, []))

        return campaign_to_wins

    def get(self, request, group_id):

        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        results['campaigns'] = self._campaign_breakdowns(group)
        return self._success(results)
