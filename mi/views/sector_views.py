from itertools import groupby
from operator import attrgetter, itemgetter

from django.db.models import Count, Min, Q, Sum
from django_countries.fields import Country as DjangoCountry

from mi.models import (
    Sector,
    SectorTeam,
    Target,
)
from mi.utils import (
    get_financial_start_date,
    month_iterator,
    sort_campaigns_by,
    two_digit_float,
)
from mi.views.base_view import BaseWinMIView
from wins.models import Notification


class BaseSectorMIView(BaseWinMIView):
    """ Abstract Base for other Sector-related MI endpoints to inherit from """

    def _get_team(self, team_id):
        """ Get SectorTeam object or False if invalid ID """

        try:
            return SectorTeam.objects.get(id=int(team_id))
        except SectorTeam.DoesNotExist:
            return False

    def _team_wins_breakdown(self, sector_team):
        """ Breakdown of team's HVC, non-HVC and non-export Wins """

        return self._breakdowns(self._get_all_wins(sector_team))

    def _get_group_wins(self, group):
        """ HVC wins of the HVC Group """
        return self._wins().filter(
            hvc__in=group.campaign_ids,
        ).select_related('confirmation')

    def _get_hvc_wins(self, team):
        """
        HVC wins alone for the `SectorTeam`

        A `Win` is considered HVC for this team, when it falls under a Campaign that belongs to this `SectorTeam`
        """
        return self._wins().filter(
            hvc__in=team.campaign_ids
        ).select_related('confirmation')

    def _get_non_hvc_wins(self, team):
        """
        non-HVC wins alone for the `SectorTeam`

        A `Win` is a non-HVC, if no HVC was mentioned while recording it
        but it belongs to a CDMS Sector that is within this `SectorTeam`s range
        """
        return self._wins().filter(
            Q(sector__in=team.sector_ids),
            Q(hvc__isnull=True) | Q(hvc='')
        ).select_related('confirmation')

    def _get_all_wins(self, sector_team):
        """ Get HVC and non-HVC Wins of a Sector Team """

        return (list(self._get_hvc_wins(sector_team)) +
                list(self._get_non_hvc_wins(sector_team)))

    def _get_avg_confirm_time(self, team):
        """
        Average of (earliest CUSTOMER notification created date - customer response date) for given team
        """

        notifications_qs = Notification.objects.filter(
            type__exact='c',
            win__sector__in=team.sector_ids,
            win__confirmation__isnull=False,
        )
        return self._average_confirm_time(notifications_qs)

    def _sector_result(self, team):
        """ Basic data about sector team - name & hvc's """

        return {
            'name': team.name,
            'avg_time_to_confirm': self._get_avg_confirm_time(team),
            'hvcs': self._hvc_overview(team.targets.all()),
        }


class TopNonHvcSectorCountryWinsView(BaseSectorMIView):
    """ Sector Team non-HVC Win data broken down by country """

    def get(self, request, team_id):
        """
        percentComplete is based on the top value being 100%
        averageWinValue is total non_hvc win value for the sector/total number of wins during the financial year
        averageWinPercent is therefore averageWinValue * 100/Total win value for the sector/market
        """
        team = self._get_team(team_id)
        if not team:
            return self._invalid('team not found')

        records_to_retreive = 5

        wins = self._wins().filter(
            Q(hvc='') | Q(hvc__isnull=True),
            sector__in=team.sector_ids,
        ).values(
            'country',
            'sector'
        ).annotate(
            total_value=Sum('total_expected_export_value'),
            total_wins=Count('id')
        ).order_by('-total_value')[:records_to_retreive]

        if not wins:
            results = []
        else:
            top_value = int(wins[0]['total_value'])

            results = [
                {
                    'region': DjangoCountry(agg_win['country']).name,
                    'sector': Sector.objects.get(id=agg_win['sector']).name,
                    'totalValue': agg_win['total_value'],
                    'totalWins': agg_win['total_wins'],
                    'percentComplete': int(int(agg_win['total_value']) * 100 / top_value),
                    'averageWinValue': int(agg_win['total_value'] / agg_win['total_wins']),
                    'averageWinPercent': int((agg_win['total_value'] / agg_win['total_wins']) * 100 / top_value)
                }
                for agg_win in wins
                ]
        return self._success(results)


class AverageTimeToConfirmView(BaseWinMIView):
    """  Average number of days to confirm a Win """

    average_time = 0.0

    def get(self, request):
        """
            Average of (earliest CUSTOMER notification created date - customer response date)
        """
        notifications = Notification.objects.filter(
            type__exact='c',
            win__confirmation__created__isnull=False
        ).annotate(Min('created')).select_related('win__confirmation')

        confirm_delay = [(notification.win.confirmation.created - notification.created).days
                         for notification in notifications]
        total_days = sum(confirm_delay)
        average_time = total_days / notifications.count()

        results = {
            'average': two_digit_float(average_time),
        }
        return self._success(results)


class SectorTeamsListView(BaseSectorMIView):
    """ Basic information about all Sector Teams """

    def _get_hvc_groups_for_team(self, team):
        """ return sorted list of HVC Groups for a given Sector Team """

        results = [
            {
                'id': hvc_group.id,
                'name': hvc_group.name,
            }
            for hvc_group in team.hvc_groups.all()
            ]
        return sorted(results, key=itemgetter('name'))

    def get(self, request):
        results = [
            {
                'id': sector_team.id,
                'name': sector_team.name,
                'hvc_groups': self._get_hvc_groups_for_team(sector_team)
            }
            for sector_team in SectorTeam.objects.all()
            ]
        return self._success(sorted(results, key=itemgetter('name')))


class SectorTeamDetailView(BaseSectorMIView):
    """ Sector Team name, targets and win-breakdown """

    def get(self, request, team_id):
        team = self._get_team(team_id)
        if not team:
            return self._invalid('team not found')

        results = self._sector_result(team)
        results['wins'] = self._team_wins_breakdown(team)
        return self._success(results)


class SectorTeamMonthsView(BaseSectorMIView):
    """ Sector Team name, hvcs and wins broken down by month """

    def _month_breakdowns(self, wins):
        month_to_wins = self._group_wins_by_month(wins)
        return [
            {
                'date': date_str,
                'totals': self._breakdowns_cumulative(month_wins),
            }
            for date_str, month_wins in month_to_wins
            ]

    def _group_wins_by_month(self, wins):
        date_attrgetter = attrgetter('date')
        sorted_wins = sorted(wins, key=date_attrgetter)
        month_to_wins = []
        # group wins by date (month-year)
        for k, g in groupby(sorted_wins, key=date_attrgetter):
            month_wins = list(g)
            date_str = month_wins[0].date.strftime('%Y-%m')
            month_to_wins.append((date_str, month_wins))

        # Add missing months within the financial year until current month
        for item in month_iterator(get_financial_start_date()):
            date_str = '{:d}-{:02d}'.format(*item)
            existing = [m for m in month_to_wins if m[0] == date_str]
            if len(existing) == 0:
                month_to_wins.append((date_str, list()))

        return sorted(month_to_wins, key=lambda tup: tup[0])

    def get(self, request, team_id):
        team = self._get_team(team_id)
        if not team:
            return self._invalid('team not found')

        results = self._sector_result(team)
        wins = self._get_all_wins(team)
        results['months'] = self._month_breakdowns(wins)
        return self._success(results)


class SectorTeamCampaignsView(BaseSectorMIView):
    """ Sector Team Wins broken down by individual HVC """

    def _campaign_breakdowns(self, team):

        wins = self._get_hvc_wins(team)
        targets = team.targets.all()
        campaign_to_wins = self._group_wins_by_target(wins, targets)
        campaigns = [
            {
                'campaign': campaign.name.split(':')[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]

        sorted_campaigns = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        return sorted_campaigns

    def get(self, request, team_id):
        team = self._get_team(team_id)
        if not team:
            return self._invalid('team not found')

        results = self._sector_result(team)
        results['campaigns'] = self._campaign_breakdowns(team)
        return self._success(results)


class SectorTeamsOverviewView(BaseSectorMIView):
    """ Overview of HVCs, targets etc. for each SectorTeam """

    def _sector_obj_data(self, sector_obj):
        """ Get general data from SectorTeam or HVCGroup """

        targets = sector_obj.targets.all()
        hvc_wins = self._get_hvc_wins(sector_obj)

        hvc_export_confirmed = sum(w.total_expected_export_value for w in hvc_wins if w.confirmed)
        hvc_export_unconfirmed = sum(w.total_expected_export_value for w in hvc_wins if not w.confirmed)
        total_target = sum(t.target for t in targets)

        hvc_colours_count = self._colours(hvc_wins, targets)

        return {
            'id': sector_obj.id,
            'name': sector_obj.name,
            'values': {
                'hvc': {
                    'current': {
                        'confirmed': hvc_export_confirmed,
                        'unconfirmed': hvc_export_unconfirmed
                    },
                    'target': total_target,
                    'target_percent': self._overview_target_percentage(hvc_wins, total_target),
                },
            },
            'hvc_performance': hvc_colours_count,
        }

    def _sector_data(self, sector_team):
        """ Calculate overview for a sector team """

        result = self._sector_obj_data(sector_team)

        hvc_wins = self._get_hvc_wins(sector_team)
        non_hvc_wins = self._get_non_hvc_wins(sector_team)
        non_hvc_confirmed = sum(w.total_expected_export_value for w in non_hvc_wins if w.confirmed)
        non_hvc_unconfirmed = sum(w.total_expected_export_value for w in non_hvc_wins if not w.confirmed)
        hvc_confirmed = result['values']['hvc']['current']['confirmed']
        hvc_unconfirmed = result['values']['hvc']['current']['unconfirmed']

        total_win_percent = self._overview_win_percentages(hvc_wins, non_hvc_wins)

        totals = {
            'confirmed': hvc_confirmed + non_hvc_confirmed,
            'unconfirmed': hvc_unconfirmed + non_hvc_unconfirmed
        }

        non_hvc_data = {
            'total_win_percent': total_win_percent['non_hvc'],
            'current': {
                'confirmed': non_hvc_confirmed,
                'unconfirmed': non_hvc_unconfirmed
            }
        }

        result['values']['totals'] = totals
        result['values']['non_hvc'] = non_hvc_data
        result['values']['hvc']['total_win_percent'] = total_win_percent['hvc']

        result['hvc_groups'] = [
            self._sector_obj_data(parent)
            for parent in sector_team.hvc_groups.all()
            ]
        return result

    def get(self, request):
        result = [self._sector_data(team) for team in SectorTeam.objects.all()]
        return self._success(sorted(result, key=lambda x: (x['name'])))
