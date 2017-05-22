from itertools import groupby
from operator import attrgetter, itemgetter

from mi.models import OverseasRegion
from mi.utils import month_iterator, sort_campaigns_by
from mi.views.base_view import BaseWinMIView


class BaseOverseasRegionsMIView(BaseWinMIView):
    """ Abstract Base for other Region-related MI endpoints to inherit from """

    def _get_region(self, region_id):
        """ Return `OverseasRegion` object for the given region_id"""
        try:
            return OverseasRegion.objects.get(id=int(region_id))
        except OverseasRegion.DoesNotExist:
            return False

    def _regions_for_fin_year(self):
        """ Returns overseas region based on countries from Targets for the given financial year """
        return OverseasRegion.objects.filter(countries__targets__financial_year=self.fin_year).distinct()

    def _get_region_wins(self, region):
        """
        All HVC and non-HVC wins for the `OverseasRegion`

        """
        return self._wins().filter(
            country__in=region.country_ids,
        )

    def _get_region_hvc_wins(self, region):
        """ HVC wins alone for the `OverseasRegion` """
        return self._wins().filter(hvc__in=region.campaign_ids)

    def _get_region_non_hvc_wins(self, region):
        """ non-HVC wins alone for the `OverseasRegion` """
        return self._non_hvc_wins().filter(country__in=region.country_ids)

    def _region_result(self, region):
        """ Basic data about region - name & hvc's """
        return {
            'name': region.name,
            'avg_time_to_confirm': self._average_confirm_time(win__country__in=region.country_ids),
            'hvcs': self._hvc_overview(region.targets),
        }


class OverseasRegionsListView(BaseOverseasRegionsMIView):
    """ List all Overseas Regions """

    def get(self, request):
        response = self._handle_fin_year(request)
        if response:
            return response

        if response:
            return response

        results = [
            {
                'id': region.id,
                'name': region.name,
            }
            for region in self._regions_for_fin_year()
            ]
        return self._success(sorted(results, key=itemgetter('name')))


class OverseasRegionDetailView(BaseOverseasRegionsMIView):
    """ Overseas Region detail view along with win-breakdown"""

    def get(self, request, region_id):
        response = self._handle_fin_year(request)
        if response:
            return response

        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')
        results = self._region_result(region)
        wins = self._get_region_wins(region)
        results['wins'] = self._breakdowns(wins)
        self._fill_date_ranges()
        return self._success(results=results)


class OverseasRegionMonthsView(BaseOverseasRegionsMIView):
    """ Overseas Region name, hvcs and wins broken down by month """

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
        sorted_wins = sorted(wins, key=self._win_date_for_grouping)
        month_to_wins = []
        for k, g in groupby(sorted_wins, key=self._win_date_for_grouping):
            month_wins = list(g)
            date_str = month_wins[0].date.strftime('%Y-%m')
            month_to_wins.append((date_str, month_wins))

        # Add missing months within the financial year until current month
        for item in month_iterator(self.fin_year):
            date_str = '{:d}-{:02d}'.format(*item)
            existing = [m for m in month_to_wins if m[0] == date_str]
            if len(existing) == 0:
                # add missing month and an empty list
                month_to_wins.append((date_str, list()))

        return sorted(month_to_wins, key=lambda tup: tup[0])

    def get(self, request, region_id):
        response = self._handle_fin_year(request)
        if response:
            return response

        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        results = self._region_result(region)
        wins = self._get_region_wins(region)
        results['months'] = self._month_breakdowns(wins)
        self._fill_date_ranges()
        return self._success(results)


class OverseasRegionCampaignsView(BaseOverseasRegionsMIView):
    """ Overseas Region's HVC's view along with their win-breakdown """

    def _campaign_breakdowns(self, region):
        wins = self._get_region_hvc_wins(region)
        campaign_to_wins = self._group_wins_by_target(wins, region.targets)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]

        sorted_campaigns = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        return sorted_campaigns

    def get(self, request, region_id):
        self._handle_fin_year(request)

        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        results = self._region_result(region)
        results['campaigns'] = self._campaign_breakdowns(region)
        self._fill_date_ranges()
        return self._success(results)


class OverseasRegionsTopNonHvcWinsView(BaseOverseasRegionsMIView):
    """ Top n HVCs with win-breakdown for given Overseas Region"""

    def get(self, request, region_id):
        response = self._handle_fin_year(request)
        if response:
            return response
        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        non_hvc_wins_qs = self._get_region_non_hvc_wins(region)
        results = self._top_non_hvc(non_hvc_wins_qs)
        self._fill_date_ranges()
        return self._success(results)


class OverseasRegionOverviewView(BaseOverseasRegionsMIView):
    """ Overview view for all Overseas Regions """

    def _region_data(self, region_obj):
        """ Calculate HVC & non-HVC data for an Overseas region """

        targets = region_obj.targets
        country_ids = region_obj.country_ids
        total_countries = len(country_ids)
        total_target = sum(t.target for t in targets)

        hvc_wins = self._get_region_hvc_wins(region_obj)
        hvc_confirmed, hvc_unconfirmed = self._confirmed_unconfirmed(hvc_wins)

        non_hvc_wins = self._get_region_non_hvc_wins(region_obj)
        non_hvc_confirmed, non_hvc_unconfirmed = self._confirmed_unconfirmed(non_hvc_wins)

        target_percentage = self._overview_target_percentage(hvc_wins, total_target)
        total_win_percent = self._overview_win_percentages(hvc_wins, non_hvc_wins)
        hvc_colours_count = self._colours(hvc_wins, targets)

        result = {
            'id': region_obj.id,
            'name': region_obj.name,
            'markets': total_countries,
            'values': {
                'hvc': {
                    'current': {
                        'confirmed': hvc_confirmed,
                        'unconfirmed': hvc_unconfirmed
                    },
                    'target': total_target,
                    'target_percent': target_percentage,
                    'total_win_percent': total_win_percent['hvc']
                },
                'non_hvc': {
                    'total_win_percent': total_win_percent['non_hvc'],
                    'current': {
                        'confirmed': non_hvc_confirmed,
                        'unconfirmed': non_hvc_unconfirmed
                    }
                }
            },
            'hvc_performance': hvc_colours_count,
        }

        return result

    def get(self, request):
        response = self._handle_fin_year(request)
        if response:
            return response

        result = [self._region_data(region) for region in OverseasRegion.objects.all()]
        self._fill_date_ranges()
        return self._success(result)
