from operator import itemgetter

from django.db.models import Count, Sum
from django_countries.fields import Country as DjangoCountry

from mi.models import Target, Sector
from mi.utils import percentage_formatted, percentage
from mi.views.base_view import BaseWinMIView, BaseMIView
from wins.models import HVC

GLOBAL_COUNTRY_CODE='XG'

class BaseHVCDetailView(BaseWinMIView):
    def _get_campaign(self, campaign_id):
        try:
            return Target.objects.get(campaign_id=campaign_id, financial_year=self.fin_year)
        except Target.DoesNotExist:
            return False

    def _campaign_result(self, campaign):
        """ Basic data about HVC campaign """

        return {
            'name': campaign.name,
            'campaign_id': campaign.campaign_id,
            'avg_time_to_confirm': self._average_confirm_time(win__hvc=campaign.charcode),
            'hvcs': self._hvc_overview([campaign]),
        }

    def _get_hvc_wins(self, campaign):
        """ 
        wins of this HVC campaign, 
        using startswith campaign_id instead of charcode 
        to cover last FYs wins that were confirmed this FY 
        """
        return self._wins().filter(hvc__startswith=campaign.campaign_id)


class HVCDetailView(BaseHVCDetailView):
    """ HVC name, targets and win-breakdown """

    def _campaign_wins_breakdown(self, campaign):
        """ 
        Breakdown of HVC
        {
            "progress": {
                "status": "red",
                "confirmed_percent": 2.0,
                "unconfirmed_percent": 0
            },
            "totals": {
                "value": {
                    "grand_total": 1376700,
                    "unconfirmed": 0,
                    "confirmed": 1376700
                },
                "number": {
                    "grand_total": 2,
                    "unconfirmed": 0,
                    "confirmed": 2
                }
            }
        }
        """

        breakdown = self._breakdowns(self._get_hvc_wins(campaign), include_non_hvc=False)
        confirmed_value = breakdown['export']['hvc']['value']['confirmed']
        unconfirmed_value = breakdown['export']['hvc']['value']['unconfirmed']
        confirmed_number = breakdown['export']['hvc']['number']['confirmed']
        unconfirmed_number = breakdown['export']['hvc']['number']['unconfirmed']
        confirmed_percent = percentage_formatted(confirmed_value, campaign.target)
        unconfirmed_percent = percentage_formatted(unconfirmed_value, campaign.target)
        result = {
            'totals': {
                'value': {
                    'confirmed': confirmed_value,
                    'unconfirmed': unconfirmed_value,
                    'grand_total': confirmed_value + unconfirmed_value,
                },
                'number': {
                    'confirmed': confirmed_number,
                    'unconfirmed': unconfirmed_number,
                    'grand_total': confirmed_number + unconfirmed_number,
                },
            },
            'progress': {
                'confirmed_percent': confirmed_percent,
                'unconfirmed_percent': unconfirmed_percent,
                'status': self._get_status_colour(campaign.target, confirmed_value),
            }
        }
        return result

    def get(self, request, campaign_id):
        response = self._handle_fin_year(request)
        if response:
            return response
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return self._not_found()

        results = self._campaign_result(campaign)
        results['wins'] = self._campaign_wins_breakdown(campaign)
        self._fill_date_ranges()
        return self._success(results)


class HVCWinsByMarketSectorView(BaseHVCDetailView):

    def _wins_by_top_sector_market(self, hvc_wins_qs):
        """ Get dict of data about HVC wins by market and sector

        percentComplete is based on the top value being 100%
        averageWinValue is total non_hvc win value for the sector/total number of wins during the financial year
        averageWinPercent is therefore averageWinValue * 100/Total win value for the sector/market

        """
        hvc_wins = hvc_wins_qs.values(
            'country',
            'sector'
        ).annotate(
            total_value=Sum('total_expected_export_value'),
            total_wins=Count('id')
        ).order_by('-total_value')

        # make a lookup to get names efficiently
        sector_id_to_name = {s.id: s.name for s in Sector.objects.all()}
        top_value = int(hvc_wins[0]['total_value']) if hvc_wins else None
        return [
            {
                'region': DjangoCountry(w['country']).name,
                'sector': sector_id_to_name[w['sector']],
                'totalValue': w['total_value'],
                'totalWins': w['total_wins'],
                'percentComplete': int(percentage(w['total_value'], top_value)),
                'averageWinValue': int(w['total_value'] / w['total_wins']),
                'averageWinPercent': int(percentage((w['total_value'] / w['total_wins']), top_value)),
            }
            for w in hvc_wins
        ]

    def get(self, request, campaign_id):
        response = self._handle_fin_year(request)
        if response:
            return response
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return self._not_found()

        hvc_wins_qs = self._get_hvc_wins(campaign)
        results = self._wins_by_top_sector_market(hvc_wins_qs)
        self._fill_date_ranges()
        return self._success(results)


class WinTableView(BaseHVCDetailView):
    """ Wins for table view for HVC"""
    def get(self, request, campaign_id):
        def confirmed_date(win):
            if not win['confirmation__created']:
                return None
            else:
                return win['confirmation__created']

        def status(win):
            if not win['notifications__created']:
                return 'email_not_sent'
            elif not win['confirmation__created']:
                return 'response_not_received'
            elif win["confirmation__agree_with_win"]:
                return 'customer_confirmed'
            else:
                return 'customer_rejected'

        def credit(win):
            return self._win_status(win) == 'confirmed'

        response = self._handle_fin_year(request)
        if response:
            return response
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return self._not_found()

        wins = self._get_hvc_wins(campaign)
        results = [
            {
                "id": win["id"],
                "company": {
                    "name": win["company_name"],
                    "cdms_id": win["cdms_reference"]
                },
                "hvc": {
                    "code": campaign_id,
                    "name": campaign.name,
                },
                "lead_officer": {
                    "name": win["lead_officer_name"],
                },
                "credit": credit(win),
                "win_date": confirmed_date(win),
                "export_amount": win["total_expected_export_value"],
                "status": status(win)
            }
            for win in wins
        ]
        self._fill_date_ranges()
        return self._success(results)


class GlobalHVCListView(BaseMIView):

    def _get_global_hvcs(self):
        return HVC.objects.filter(campaign_id__in=
            Target.objects.for_fin_year(
                fin_year=self.fin_year)
                    .filter(country__country=GLOBAL_COUNTRY_CODE)
                    .values_list('campaign_id')
        )

    def get(self, request):
        response = self._handle_fin_year(request)
        if response:
            return response

        results = [
            {
                'code': hvc.campaign_id,
                'name': hvc.name,
            }
            for hvc in self._get_global_hvcs()
        ]
        self._fill_date_ranges()
        return self._success(sorted(results, key=itemgetter('name')))
