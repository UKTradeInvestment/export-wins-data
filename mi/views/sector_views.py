import operator
from collections import defaultdict
from itertools import groupby
from operator import itemgetter
from functools import reduce

from django.db.models import Q

from mi.models import (
    HVCGroup,
    SectorTeam,
    Target,
)
from mi.utils import sort_campaigns_by
from mi.views.base_view import BaseWinMIView


def get_campaigns_from_group(g: HVCGroup, **kwargs):
    return g.campaign_ids


def get_campaigns_from_group_for_year(g: HVCGroup, fin_year=None):
    return g.fin_year_campaign_ids(fin_year)


class BaseSectorMIView(BaseWinMIView):
    """ Abstract Base for other Sector-related MI endpoints to inherit from """

    def _hvc_groups_for_fin_year(self):
        """ extracts hvc groups from targets for the given financial year """
        return HVCGroup.objects.filter(targets__financial_year=self.fin_year).distinct()

    def _hvc_groups_for_team(self, team):
        """ `HVCGroup` objects for a `SectorTeam` """
        return self._hvc_groups_for_fin_year().filter(sector_team=team)

    def _sector_teams_for_fin_year(self):
        """ Returns sector teams based on hvc groups from Targets for the given financial year """
        return SectorTeam.objects.filter(hvc_groups__targets__financial_year=self.fin_year).distinct()

    def _get_team(self, team_id):
        """ Get SectorTeam object or False if invalid ID """
        try:
            return SectorTeam.objects.get(id=int(team_id))
        except SectorTeam.DoesNotExist:
            return False

    def _team_wins_breakdown(self, sector_team):
        """ Breakdown of team's HVC, non-HVC and non-export Wins """
        return self._breakdowns(
            self._get_hvc_wins(sector_team),
            non_hvc_wins=self._get_non_hvc_wins(sector_team)
        )

    def _get_group_fn(self, group, fn):
        """
        Overriding default group.campaign_ids, to add a hack to cater for
        cross FY team changes.
        """
        campaign_ids = fn(group, fin_year=self.fin_year)
        if group.name == "Consumer and Retail":
            other_group = HVCGroup.objects.get(name="Consumer Goods & Retail")
            campaign_ids.extend(fn(other_group, fin_year=self.fin_year))
        elif group.name == "Creative":
            other_group = HVCGroup.objects.get(name="Creative Industries")
            campaign_ids.extend(fn(other_group, fin_year=self.fin_year))
        elif group.id == 34:  # Sports Economy has same name across
            other_group = HVCGroup.objects.get(id=27)
            campaign_ids.extend(fn(other_group, fin_year=self.fin_year))
        elif group.id == 30:
            fin_group = HVCGroup.objects.get(name="Financial Services")
            campaign_ids.extend(fn(fin_group, fin_year=self.fin_year))
            pro_group = HVCGroup.objects.get(name="Professional Services")
            campaign_ids.extend(fn(pro_group, fin_year=self.fin_year))
        elif group.id == 29:
            fin_group = HVCGroup.objects.get(name="Digital Economy")
            campaign_ids.extend(fn(fin_group, fin_year=self.fin_year))
        return campaign_ids

    def _get_group_campaigns_for_year(self, group):
        return self._get_group_fn(group, get_campaigns_from_group_for_year)

    def _get_group_campaigns(self, group):
        return self._get_group_fn(group, get_campaigns_from_group)

    def _get_group_wins(self, group):
        """ HVC wins of the HVC Group, for given `FinancialYear` """
        group_hvcs = [hvc[:4] for hvc in self._get_group_campaigns_for_year(group)]
        filter = reduce(
            operator.or_, [Q(hvc__startswith=hvc) for hvc in group_hvcs])
        return self._hvc_wins().filter(filter)

    def _get_team_campaigns(self, team):
        """
        Overriding default team.campaign_ids, to add a hack to cater for cross FY team changes
        """
        # hack for Consumer & Creative
        campaign_ids = team.campaign_ids
        if team.name == "Creative, Consumer and Sports":
            other_team = SectorTeam.objects.get(name="Consumer & Creative")
            campaign_ids.extend(other_team.campaign_ids)
        return campaign_ids

    def _get_hvc_wins(self, team):
        """ HVC wins alone for the `SectorTeam`
        A `Win` is considered HVC for this team, when it falls under a Campaign that belongs to this `SectorTeam`
        """
        return self._hvc_wins().filter(hvc__in=self._get_team_campaigns(team))

    def _get_non_hvc_wins(self, team):
        """ non-HVC wins alone for the `SectorTeam`

        A `Win` is a non-HVC, if no HVC was mentioned while recording it
        but it belongs to a CDMS Sector that is within this `SectorTeam`s range

        """
        return self._non_hvc_wins().filter(sector__in=team.sector_ids)

    def _get_all_wins(self, sector_team):
        """ Get HVC and non-HVC Wins of a Sector Team """

        return self._get_hvc_wins(sector_team) | self._get_non_hvc_wins(sector_team)

    def _sector_result(self, team):
        """ Basic data about sector team - name & hvc's """

        return {
            'name': team.name,
            'avg_time_to_confirm': self._average_confirm_time(win__sector__in=team.sector_ids),
            'hvcs': self._hvc_overview(team.fin_year_targets(fin_year=self.fin_year)),
        }


class TopNonHvcSectorCountryWinsView(BaseSectorMIView):
    """ Sector Team non-HVC Win data broken down by country """

    def get(self, request, team_id):
        team = self._get_team(team_id)
        if not team:
            return self._invalid('team not found')
        non_hvc_wins_qs = self._get_non_hvc_wins(team)
        results = self._top_non_hvc(non_hvc_wins_qs)
        return self._success(results)


class SectorTeamsListView(BaseSectorMIView):
    """ Basic information about all Sector Teams """

    def _hvc_groups_data(self, team):
        """ return sorted list of HVC Groups data for a given Sector Team """

        results = [
            {
                'id': hvc_group.id,
                'name': hvc_group.name,
            }
            for hvc_group in self._hvc_groups_for_team(team)
        ]
        return sorted(results, key=itemgetter('name'))

    def get(self, request):
        results = [
            {
                'id': sector_team.id,
                'name': sector_team.name,
                'hvc_groups': self._hvc_groups_data(sector_team)
            }
            for sector_team in self._sector_teams_for_fin_year()
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
        targets = team.fin_year_targets(self.fin_year)
        campaign_to_wins = self._group_wins_by_target(wins, targets)
        campaigns = [
            {
                'campaign': campaign.name.split(':')[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]

        sorted_campaigns = sorted(
            campaigns, key=sort_campaigns_by, reverse=True)
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_groups = defaultdict(list)
        self.team_targets = defaultdict(list)
        self.sector_to_wins = defaultdict(list)
        self.hvc_to_wins = defaultdict(list)

    def _get_cached_hvc_wins(self, campaign_ids):
        return [win
                for code, wins in self.hvc_to_wins.items() if code in campaign_ids
                for win in wins
                ]

    def _get_cached_non_hvc_wins(self, sector_ids):
        return [win
                for sector, wins in self.sector_to_wins.items() if sector in sector_ids
                for win in wins
                ]

    def _sector_obj_data(self, sector_obj, campaign_ids):
        """ Get general data from SectorTeam or HVCGroup """

        sector_targets = self.team_targets[sector_obj]
        total_target = sum([t.target for t in sector_targets])
        hvc_wins = self._get_cached_hvc_wins(campaign_ids)
        hvc_confirmed, hvc_unconfirmed = self._confirmed_unconfirmed(hvc_wins)
        hvc_colours_count = self._colours(hvc_wins, sector_targets)

        return {
            'id': sector_obj.id,
            'name': sector_obj.name,
            'values': {
                'hvc': {
                    'current': {
                        'confirmed': hvc_confirmed,
                        'unconfirmed': hvc_unconfirmed
                    },
                    'target': total_target,
                    'target_percent': self._overview_target_percentage(hvc_wins, total_target),
                },
            },
            'hvc_performance': hvc_colours_count,
        }

    def _sector_data(self, sector_team):
        """ Calculate overview for a sector team """

        team_campaign_ids = self._get_team_campaigns(sector_team)
        result = self._sector_obj_data(sector_team, team_campaign_ids)
        hvc_wins = self._get_cached_hvc_wins(team_campaign_ids)
        non_hvc_wins = self._get_cached_non_hvc_wins(sector_team.sector_ids)
        non_hvc_confirmed, non_hvc_unconfirmed = self._confirmed_unconfirmed(
            non_hvc_wins)
        hvc_confirmed = result['values']['hvc']['current']['confirmed']
        hvc_unconfirmed = result['values']['hvc']['current']['unconfirmed']
        total_win_percent = self._overview_win_percentages(
            hvc_wins, non_hvc_wins)
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
        groups = self.team_groups[sector_team]
        result['hvc_groups'] = [self._sector_obj_data(
            g, self._get_group_campaigns(g)) for g in groups]
        return result

    def get(self, request):

        # cache wins to avoid many queries
        hvc_wins, non_hvc_wins = self._wins().hvc(
            fin_year=self.fin_year), self._wins().non_hvc(fin_year=self.fin_year)
        for win in hvc_wins:
            self.hvc_to_wins[win['hvc']].append(win)
        for win in non_hvc_wins:
            self.sector_to_wins[win['sector']].append(win)

        # cache targets
        targets = Target.objects.filter(
            financial_year=self.fin_year).select_related('hvc_group', 'sector_team')
        for target in targets:
            self.team_targets[target.sector_team].append(target)
            self.team_targets[target.hvc_group].append(target)

        # cache groups
        for group in self._hvc_groups_for_fin_year():
            self.team_groups[group.sector_team].append(group)

        sector_team_qs = self._sector_teams_for_fin_year().prefetch_related(
            'sectors',
            'targets',
            'hvc_groups',
            'hvc_groups__targets',
        )

        result = [self._sector_data(team) for team in sector_team_qs]

        return self._success(sorted(result, key=itemgetter('name')))


class SectorTeamWinTableView(BaseSectorMIView):

    def get(self, request, team_id):
        team = self._get_team(team_id)
        if not team:
            return self._not_found()

        results = {
            "sector_team": {
                "id": team_id,
                "name": team.name,
            },
            "wins": self._win_table_wins(self._get_hvc_wins(team), self._get_non_hvc_wins(team))
        }
        return self._success(results)
