import operator
from functools import reduce
from itertools import groupby
from operator import itemgetter

from django.db.models import Q

from django_countries.fields import Country as DjangoCountry

from mi.models import Country
from mi.views.base_view import BaseWinMIView, BaseMIView
from mi.utils import sort_campaigns_by


class BaseCountriesMIView(BaseWinMIView):
    """ Abstract Base for other Country-related MI endpoints to inherit from """

    country = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        country_code = kwargs.get('country_code')
        self.country = self._get_country(country_code=country_code)
        if not self.country:
            self._not_found('Country {} not found'.format(country_code))


    def _get_country(self, country_code):
        try:
            return Country.objects.get(country=country_code)
        except Country.DoesNotExist:
            return False

    def _get_hvc_wins(self, country):
        dj_country = DjangoCountry(country.country.code)
        wins = self._hvc_wins().filter(country__exact=dj_country)
        return wins

    def _get_non_hvc_wins(self, country):
        dj_country = DjangoCountry(country.country.code)
        return self._non_hvc_wins().filter(country__exact=dj_country)

    def _get_all_wins(self, country):
        return self._get_hvc_wins(country) | self._get_non_hvc_wins(country)

    def _country_result(self, country):
        """ Basic data about countries - name & hvc's """
        dj_country = DjangoCountry(country.country.code)
        return {
            'name': country.country.name,
            'avg_time_to_confirm': self._average_confirm_time(win__country__exact=dj_country),
            'hvcs': self._hvc_overview(country.fin_year_targets(fin_year=self.fin_year)),
        }


class CountryListView(BaseMIView):
    """ List all countries """

    def get(self, request):
        results = [
            {
                'id': c.id,
                'code': c.country.code,
                'name': c.country.name
            }
            for c in Country.objects.all()
        ]
        return self._success(sorted(results, key=itemgetter('name')))


class CountryDetailView(BaseCountriesMIView):
    """ Country details and wins breakdown """

    def get(self, request, country_code):
        results = self._country_result(self.country)
        hvc_wins = self._get_hvc_wins(self.country)
        non_hvc_wins = self._get_non_hvc_wins(self.country)
        results['wins'] = self._breakdowns(hvc_wins, non_hvc_wins=non_hvc_wins)
        return self._success(results)


class CountryMonthsView(BaseCountriesMIView):
    """ Country name, hvcs and wins broken down by month """

    def get(self, request, country_code):
        results = self._country_result(self.country)
        wins = self._get_all_wins(self.country)

        results['months'] = self._month_breakdowns(wins)
        return self._success(results)


class CountryCampaignsView(BaseCountriesMIView):
    """ Country HVC's view along with their win-breakdown """

    def _campaign_breakdowns(self, country):
        wins = self._get_hvc_wins(country)
        campaign_to_wins = self._group_wins_by_target(wins, country.fin_year_targets(self.fin_year))
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]
        sorted_campaigns = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        return sorted_campaigns

    def get(self, request, country_code):
        results = self._country_result(self.country)
        results['campaigns'] = self._campaign_breakdowns(self.country)
        return self._success(results)


class CountryTopNonHvcWinsView(BaseCountriesMIView):

    def get(self, request, country_code):
        non_hvc_wins_qs = self._get_non_hvc_wins(self.country)
        results = self._top_non_hvc(non_hvc_wins_qs)
        return self._success(results)


class CountryWinTableView(BaseCountriesMIView):

    def get(self, request, country_code):
        results = {
            "country": {
                "id": country_code,
                "name": self.country.country.name,
            },
            "wins": self._win_table_wins(self._get_hvc_wins(self.country), self._get_non_hvc_wins(self.country))
        }
        return self._success(results)
