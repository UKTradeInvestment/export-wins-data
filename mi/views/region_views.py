import operator
from functools import reduce
from itertools import groupby
from operator import itemgetter

from django.db.models import Q

from mi.models import OverseasRegion, OverseasRegionGroup
from mi.serializers import OverseasRegionGroupSerializer
from mi.utils import sort_campaigns_by
from mi.views.base_view import BaseWinMIView, BaseExportMIView


class BaseOverseasRegionGroupMIView(BaseExportMIView):

    def get_queryset(self):
        return OverseasRegionGroup.objects.all()

    def get_results(self):
        return [OverseasRegionGroupSerializer(instance=x, year=self.fin_year).data for x in self.get_queryset().order_by('name')]

    def get(self, request):
        return self._success(self.get_results())


class BaseOverseasRegionsMIView(BaseWinMIView):
    """ Abstract Base for other Region-related MI endpoints to inherit from """

    def _get_region(self, region_id):
        """ Return `OverseasRegion` object for the given region_id"""
        try:
            return self._regions_for_fin_year().get(id=int(region_id))
        except OverseasRegion.DoesNotExist:
            return False

    def _regions_for_fin_year(self):
        """ Returns overseas region based on countries from Targets for the given financial year """
        return OverseasRegion.objects.filter(
            countries__targets__financial_year_id=self.fin_year.id,
            overseasregionyear__financial_year_id=self.fin_year.id
        ).distinct()

    def _region_hvc_filter(self, region, non_contrib=False):
        """ filter to include all HVCs, irrespective of FY """

        targets = region.fin_year_targets(self.fin_year)
        if non_contrib:
            targets = targets | region.fin_year_non_contributing_targets(
                self.fin_year)
        campaign_ids = [t.campaign_id for t in targets]
        charcodes = [t.charcode for t in targets]
        region_hvc_filter = Q(
            Q(reduce(operator.or_, [Q(hvc__startswith=t)
                                    for t in campaign_ids]))
            | Q(hvc__in=charcodes)
        )
        return region_hvc_filter

    def _region_non_hvc_filter(self, region):
        """ specific filter for non-HVC, with all countries for the given region """
        region_countries = region.fin_year_country_ids(
            self.fin_year) | region.fin_year_non_contributing_country_ids(self.fin_year)
        region.fin_year_non_contributing_country_ids(self.fin_year)
        region_non_hvc_filter = Q(
            Q(hvc__isnull=True) | Q(hvc='')) & Q(country__in=region_countries)
        return region_non_hvc_filter

    def _get_region_wins(self, region):
        """
        All HVC and non-HVC wins for the `OverseasRegion`
        """
        all_wins_filter = Q(self._region_hvc_filter(
            region) | self._region_non_hvc_filter(region))
        wins = self._wins().filter(all_wins_filter)
        return wins

    def _get_region_hvc_wins(self, region, non_contrib=False):
        """ HVC wins alone for the `OverseasRegion` """
        wins = self._hvc_wins().filter(self._region_hvc_filter(region, non_contrib))
        return wins

    def _get_region_non_hvc_wins(self, region):
        """ non-HVC wins alone for the `OverseasRegion` """
        return self._non_hvc_wins().filter(self._region_non_hvc_filter(region))

    def _region_result(self, region):
        """ Basic data about region - name & hvc's """
        return {
            'name': region.name,
            'avg_time_to_confirm': self._average_confirm_time(win__country__in=region.country_ids),
            'hvcs': self._hvc_overview(region.fin_year_targets(self.fin_year)),
        }


class OverseasRegionGroupListView(BaseOverseasRegionGroupMIView):
    """
    List all Overseas Region Groups for current year
    """

    def get_queryset(self):
        return super().get_queryset().filter(
            overseasregiongroupyear__financial_year=self.fin_year
        ).distinct()


class OverseasRegionsListView(BaseOverseasRegionsMIView):
    """ List all Overseas Regions """

    def get(self, request):
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
        region = self._get_region(region_id)
        if not region:
            return self._not_found()
        results = self._region_result(region)
        hvc_wins, non_hvc_wins = self._get_region_hvc_wins(
            region), self._get_region_non_hvc_wins(region)
        results['wins'] = self._breakdowns(
            hvc_wins=hvc_wins, non_hvc_wins=non_hvc_wins)
        return self._success(results=results)


class OverseasRegionMonthsView(BaseOverseasRegionsMIView):
    """ Overseas Region name, hvcs and wins broken down by month """

    def get(self, request, region_id):
        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        results = self._region_result(region)
        wins = self._get_region_wins(region)

        results['months'] = self._month_breakdowns(wins)
        return self._success(results)


class OverseasRegionCampaignsView(BaseOverseasRegionsMIView):
    """ Overseas Region's HVC's view along with their win-breakdown """

    def _campaign_breakdowns(self, region):
        wins = self._get_region_hvc_wins(region, non_contrib=True)
        all_targets = region.fin_year_targets(
            self.fin_year) | region.fin_year_non_contributing_targets(self.fin_year)
        campaign_to_wins = self._group_wins_by_target(wins, all_targets)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]

        sorted_campaigns = sorted(
            campaigns, key=sort_campaigns_by, reverse=True)
        return sorted_campaigns

    def get(self, request, region_id):
        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        results = self._region_result(region)
        results['campaigns'] = self._campaign_breakdowns(region)
        return self._success(results)


class OverseasRegionsTopNonHvcWinsView(BaseOverseasRegionsMIView):
    """ Top n HVCs with win-breakdown for given Overseas Region"""

    def get(self, request, region_id):
        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        non_hvc_wins_qs = self._get_region_non_hvc_wins(region)
        results = self._top_non_hvc(non_hvc_wins_qs)
        return self._success(results)


class OverseasRegionOverviewView(BaseOverseasRegionsMIView):
    """ Overview view for all Overseas Regions """

    def _region_data(self, region_obj):
        """ Calculate HVC & non-HVC data for an Overseas region """

        targets = region_obj.fin_year_targets(self.fin_year)
        country_ids = region_obj.fin_year_country_ids(self.fin_year)
        total_countries = len(country_ids)
        total_target = sum(t.target for t in targets)

        hvc_wins = self._get_region_hvc_wins(region_obj)
        hvc_confirmed, hvc_unconfirmed = self._confirmed_unconfirmed(hvc_wins)

        non_hvc_wins = self._get_region_non_hvc_wins(region_obj)
        non_hvc_confirmed, non_hvc_unconfirmed = self._confirmed_unconfirmed(
            non_hvc_wins)

        target_percentage = self._overview_target_percentage(
            hvc_wins, total_target)
        total_win_percent = self._overview_win_percentages(
            hvc_wins, non_hvc_wins)
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
        result = [self._region_data(region)
                  for region in self._regions_for_fin_year()]
        return self._success(result)


class OverseasRegionWinTableView(BaseOverseasRegionsMIView):
    def get(self, request, region_id):
        region = self._get_region(region_id)
        if not region:
            return self._not_found()

        results = {
            "os_region": {
                "id": region_id,
                "name": region.name,
            },
            "wins": self._win_table_wins(self._get_region_hvc_wins(region), self._get_region_non_hvc_wins(region))
        }
        return self._success(results)
