from itertools import groupby
from operator import attrgetter

from django.db.models import Sum, Count, Q, Min
from django_countries.fields import Country as DjangoCountry

from rest_framework.generics import ListAPIView

from alice.authenticators import IsMIServer, IsMIUser
from mi.models import OverseasRegion, Target, Sector
from mi.serializers import OverseasRegionSerializer
from mi.utils import (
    get_financial_start_date,
    month_iterator,
    sort_campaigns_by,
    two_digit_float,
)
from mi.views.base_view import BaseWinMIView
from wins.models import Notification


class BaseOverseasRegionsMIView(BaseWinMIView):
    """ Abstract Base for other Region-related MI endpoints to inherit from """

    def _get_region(self, region_id):
        """ Return `OverseasRegion` object for the given region_id"""

        try:
            return OverseasRegion.objects.get(id=int(region_id))
        except OverseasRegion.DoesNotExist:
            return False

    def _get_region_wins(self, region):
        """
        All HVC and non-HVC wins for the `OverseasRegion`

        """

        return self._wins().filter(
            country__in=region.country_ids,
        ).select_related('confirmation')

    def _get_region_hvc_wins(self, region):
        """
        HVC wins alone for the `OverseasRegion`
        """
        return self._wins().filter(
            hvc__in=region.campaign_ids,
        ).select_related('confirmation')

    def _get_region_non_hvc_wins(self, region):
        """
        non-HVC wins alone for the `OverseasRegion`
        """
        return self._wins().filter(
            Q(country__in=region.country_ids),
            Q(hvc__isnull=True) | Q(hvc=''),
        ).select_related('confirmation')

    def _get_avg_confirm_time(self, region):
        """
            Average of (earliest CUSTOMER notification created date - customer response date) for given team
        """
        notifications = Notification.objects.filter(
            type__exact='c',
            win__country__in=region.country_ids,
            win__confirmation__created__isnull=False
        ).annotate(Min('created')).select_related('win__confirmation')

        if notifications.count() == 0:
            return two_digit_float(0)

        confirm_delay = [(notification.win.confirmation.created - notification.created).days
                         for notification in notifications]
        total_days = sum(confirm_delay)
        average_time = total_days / notifications.count()

        return two_digit_float(average_time)

    def _region_result(self, region):
        """ Basic data about region - name & hvc's """
        return {
            'name': region.name,
            'avg_time_to_confirm': self._get_avg_confirm_time(region),
            'hvcs': self._hvc_overview(region.targets),
        }


class OverseasRegionsListView(ListAPIView):
    """ List all Overseas Regions """
    permission_classes = (IsMIServer, IsMIUser)
    queryset = OverseasRegion.objects.all()
    serializer_class = OverseasRegionSerializer


class OverseasRegionDetailView(BaseOverseasRegionsMIView):
    """ Overseas Region detail view along with win-breakdown"""

    def get(self, request, region_id):
        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')
        results = self._region_result(region)
        wins = self._get_region_wins(region)
        results['wins'] = self._breakdowns(wins)
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
        date_attrgetter = attrgetter('date')
        sorted_wins = sorted(wins, key=date_attrgetter)
        month_to_wins = []
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
        campaign_to_wins = self._group_wins_by_campaign(region)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
            ]

        sorted_campaigns = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        return sorted_campaigns

    def _group_wins_by_campaign(self, region):
        wins = self._get_region_hvc_wins(region)
        hvc_attrgetter = attrgetter('hvc')
        sorted_wins = sorted(wins, key=hvc_attrgetter)
        campaign_to_wins = []

        # group existing wins by campaign
        for k, g in groupby(sorted_wins, key=hvc_attrgetter):
            campaign_wins = list(g)
            campaign_to_wins.append((Target.objects.get(campaign_id=k[:-2]), campaign_wins))

        # add remaining campaigns

        for target in region.targets:
            if not any(target in campaign_to_win for campaign_to_win in campaign_to_wins):
                campaign_to_wins.append((target, []))

        return campaign_to_wins

    def get(self, request, region_id):

        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')

        results = self._region_result(region)
        results['campaigns'] = self._campaign_breakdowns(region)
        return self._success(results)


class OverseasRegionsTopNonHvcWinsView(BaseOverseasRegionsMIView):
    """ Top n HVCs with win-breakdown for given Overseas Region"""

    def _breakdown(self, agg_win):
        return {
            'region': agg_win.country.name,
            'sector': agg_win.sector.name,
            'totalValue': agg_win.total_value,
            'totalWins': agg_win.total_wins
        }

    def get(self, request, region_id):
        """
            percentComplete is based on the top value being 100%
            averageWinValue is total non_hvc win value for the sector/total number of wins during the financial year
            averageWinPercent is therefore averageWinValue * 100/Total win value for the sector/market
        """
        region = self._get_region(region_id)
        if not region:
            return self._invalid('region not found')
        country_ids = [s.country for s in region.countries.all()]
        records_to_retreive = 5
        non_hvc_wins = self._wins().filter(
            Q(hvc='') | Q(hvc__isnull=True),
            country__in=country_ids,
        ).values(
            'country',
            'sector'
        ).annotate(
            total_value=Sum('total_expected_export_value'),
            total_wins=Count('id')
        ).order_by('-total_value')[:records_to_retreive]

        top_value = int(non_hvc_wins[0]['total_value'])

        results = [
            {
                'region': DjangoCountry(agg_win['country']).name,
                'sector': Sector.objects.get(id=agg_win['sector']).name,
                'totalValue': agg_win['total_value'],
                'totalWins': agg_win['total_wins'],
                'percentComplete': int(int(agg_win['total_value']) * 100 / top_value),
                'averageWinValue': agg_win['total_value'] / agg_win['total_wins'],
                'averageWinPercent': two_digit_float(
                    (agg_win['total_value'] / agg_win['total_wins']) * 100 / int(agg_win['total_value']))
            }
            for agg_win in non_hvc_wins
            ]
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
        hvc_confirmed = sum(w.total_expected_export_value for w in hvc_wins if w.confirmed)
        hvc_unconfirmed = sum(w.total_expected_export_value for w in hvc_wins if not w.confirmed)
        non_hvc_wins = self._get_region_non_hvc_wins(region_obj)
        non_hvc_confirmed = sum(w.total_expected_export_value for w in non_hvc_wins if w.confirmed)
        non_hvc_unconfirmed = sum(w.total_expected_export_value for w in non_hvc_wins if not w.confirmed)

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
        result = [self._region_data(region) for region in OverseasRegion.objects.all()]
        return self._success(result)
