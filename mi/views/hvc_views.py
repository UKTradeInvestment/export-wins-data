from mi.models import Target
from mi.utils import percentage_formatted
from mi.views.base_view import BaseWinMIView


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
    """ Sector Team name, targets and win-breakdown """

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
                'status': self._get_status_colour(campaign.target,confirmed_value),
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