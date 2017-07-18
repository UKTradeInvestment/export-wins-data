from django_countries.fields import Country as DjangoCountry

from mi.models import Country, Target
from mi.views.base_view import BaseWinMIView, BaseMIView
from wins.models import Win


class BaseCountriesMIView(BaseWinMIView):
    """ Abstract Base for other Country-related MI endpoints to inherit from """

    def _get_country(self, country_id):
        try:
            return Country.objects.get(id=int(country_id))
        except Country.DoesNotExist:
            return False

    def _wins(self, country):
        dj_country = DjangoCountry(country.country.code)
        return super()._wins().filter(
            country__exact=dj_country,
            date__range=(get_financial_start_date(), get_financial_end_date()),
        ).select_related('confirmation')

    def _get_hvc_wins(self, country):
        return self._wins(country).hvc(fin_year=self.fin_year)

    def _get_non_hvc_wins(self, country):
        return self._wins(country).non_hvc(fin_year=self.fin_year)

    def _country_result(self, country):
        """ Basic data about countries - name & hvc's """
        return {
            'name': country.country.name,
            'hvcs': self._hvc_overview(country.targets.all()),
        }


class CountryListView(BaseMIView):
    def get(self, request):
        results = [
            {
                'id': c.id,
                'code': c.country.code,
                'name': c.country.name
            }
            for c in Country.objects.all()
            ]
        return self._success(results)


class CountryDetailView(BaseCountriesMIView):

    def get(self, request, country_id):

        country = self._get_country(country_id)
        if not country:
            return self._invalid('team not found')

        targets = Target.objects.filter(country=country)
        total_target = 0
        for target in targets:
            total_target += target.target

        results = self._country_result(country)
        hvc_wins = self._get_hvc_wins(country)
        non_hvc_wins = self._get_non_hvc_wins(country)
        results['wins'] = self._breakdowns(hvc_wins, non_hvc_wins=non_hvc_wins)
        return self._success(results)


class CountryWinsView(BaseCountriesMIView):

    def get(self, request):
        results = [
            {
                'id': c.id,
                'code': c.country.code,
                'name': c.country.name,
                'wins': self._breakdowns(self._get_hvc_wins(c), non_hvc_wins=self._get_non_hvc_wins(c))
            }
            for c in Country.objects.all()
            ]
        return self._success(results)
