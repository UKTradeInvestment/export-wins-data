import operator
from functools import reduce
from itertools import groupby
from operator import itemgetter

from django.db.models import Q

from django_countries.fields import Country as DjangoCountry

from mi.models import Country
from mi.utils import month_iterator
from mi.views.base_view import BaseWinMIView, BaseMIView
from mi.utils import sort_campaigns_by


class BaseCountriesMIView(BaseWinMIView):
    """ Abstract Base for other Country-related MI endpoints to inherit from """

    def _get_country(self, country_code):
        try:
            return Country.objects.get(country=country_code)
        except Country.DoesNotExist:
            return False

    def _country_hvc_filter(self, country):
        """ filter to include all HVCs, irrespective of FY """
        region_hvc_filter = Q(
            Q(reduce(operator.or_, 
                [Q(hvc__startswith=t) for t in country.fin_year_campaign_ids(self.fin_year)]))
            | Q(hvc__in=country.fin_year_charcodes(self.fin_year))
        )
        return region_hvc_filter

    def _country_non_hvc_filter(self, country):
        """ specific filter for non-HVC, for the given Country """
        dj_country = DjangoCountry(country.country.code)
        region_non_hvc_filter = Q(Q(hvc__isnull=True) | Q(hvc='')) & Q(country__exact=dj_country)
        return region_non_hvc_filter
    
    def _get_hvc_wins(self, country):
        wins = self._hvc_wins().filter(self._country_hvc_filter(country))
        return wins

    def _get_non_hvc_wins(self, country):
        return self._non_hvc_wins().filter(self._country_non_hvc_filter(country))

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
        country = self._get_country(country_code)
        if not country:
            return self._not_found()

        results = self._country_result(country)
        hvc_wins = self._get_hvc_wins(country)
        non_hvc_wins = self._get_non_hvc_wins(country)
        results['wins'] = self._breakdowns(hvc_wins, non_hvc_wins=non_hvc_wins)
        return self._success(results)


class CountryMonthsView(BaseCountriesMIView):
    """ Country name, hvcs and wins broken down by month """

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
            date_str = month_wins[0]['date'].strftime('%Y-%m')
            month_to_wins.append((date_str, month_wins))

        # Add missing months within the financial year until current month
        for item in month_iterator(self.fin_year):
            date_str = '{:d}-{:02d}'.format(*item)
            existing = [m for m in month_to_wins if m[0] == date_str]
            if len(existing) == 0:
                # add missing month and an empty list
                month_to_wins.append((date_str, list()))

        return sorted(month_to_wins, key=lambda tup: tup[0])

    def get(self, request, country_code):
        country = self._get_country(country_code)
        if not country:
            return self._invalid('country not found')

        results = self._country_result(country)
        wins = self._get_all_wins(country)

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
        country = self._get_country(country_code)
        if not country:
            return self._not_found()

        results = self._country_result(country)
        results['campaigns'] = self._campaign_breakdowns(country)
        return self._success(results)
