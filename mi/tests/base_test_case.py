import json

from django.utils.datetime_safe import datetime
from django.utils.timezone import get_current_timezone
from factory.fuzzy import FuzzyChoice

from fixturedb.factories.win import create_win_factory
from sso.tests.test_oauth import BaseSSOTestCase
from users.factories import UserFactory
from wins.factories import HVCFactory
from wins.models import Win
from mi.models import Sector, SectorTeam


def get_sectors_for_team(team_id):
    return list(
        Sector.objects.filter(sector_team=team_id).order_by('name').values_list('pk', flat=True)
    )


def get_hvcs_for_team(team_id):
    team = SectorTeam.objects.get(pk=team_id)
    return list(team.targets.values_list('campaign_id', flat=True))


class MiApiViewsBaseTestCase(BaseSSOTestCase):
    maxDiff = None
    fin_start_date = datetime(2016, 4, 1, tzinfo=get_current_timezone())
    frozen_date = datetime(2016, 11, 1, tzinfo=get_current_timezone())
    fin_end_date = datetime(2017, 3, 31, tzinfo=get_current_timezone())
    frozen_date_17 = datetime(2017, 5, 1, tzinfo=get_current_timezone())

    SAMPLE_COUNTRIES = ['CA', 'BS', 'GQ', 'VA', 'AQ', 'SA', 'EG', 'LU', 'ER', 'GA', 'MP']
    CAMPAIGN_TARGET = 10000000
    SECTORS_NOT_IN_EITHER_TEAM = [135, 136, 138, 139, 140, 145]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = UserFactory.create()
        cls.user.save()
        # needed to get names of HVCs, have to do again because factory
        # remembers other tests, even if flushed from DB
        sector_ids = list(Sector.objects.values_list('pk', flat=True).order_by('id'))
        sector_ids.append(6)
        for sector_id in sector_ids:
            HVCFactory.create(
                campaign_id='E%03d' % sector_id,
                financial_year=16,
            )
        cls.TEAM_1_HVCS = get_hvcs_for_team(1)[:10]
        cls.TEAM_15_HVCS = get_hvcs_for_team(15)
        cls.TEAM_1_SECTORS = get_sectors_for_team(1)
        cls.TEAM_15_SECTORS = get_sectors_for_team(15)
        cls.FIRST_TEAM_1_SECTOR = cls.TEAM_1_SECTORS[0]
        cls.SECOND_TEAM_1_SECTOR = cls.TEAM_1_SECTORS[1]

    def _get_api_response_value(self, url):
        resp = self._get_api_response(url)
        return resp.content.decode("utf-8")

    @property
    def _api_response_json(self):
        return self._get_api_response_value(self.url)

    @property
    def _api_response_data(self):
        return self._get_api_response(self.url).data["results"]

    def assertResponse(self):
        """ Helper to check that the API response is as expected

        Small abstraction to allow defining url once per TestCase/endpoint,
        so that each test method only has to define an expected response.

        """
        assert hasattr(self, 'expected_response'),\
            'expected_response not added to TestCase class'
        self.assertJSONEqual(json.dumps(self._api_response_data), self.expected_response)


class MiApiViewsWithWinsBaseTestCase(MiApiViewsBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._win_factory_function = create_win_factory(cls.user)

    def _create_win(self, hvc_code, sector_id=None, win_date=None, export_value=None,
                    confirm=False, agree_with_win=True, notify_date=None, response_date=None, country=None,
                    fin_year=2016, **kwargs):
        """ generic function creating `Win`
        :rtype: `Win`
        """
        win = self._win_factory_function(
            hvc_code,
            sector_id=sector_id,
            win_date=win_date,
            export_value=export_value,
            confirm=confirm,
            agree_with_win=agree_with_win,
            notify_date=notify_date,
            response_date=response_date,
            country=country,
            fin_year=fin_year,
            **kwargs
        )
        return win

    def _create_hvc_win(self, hvc_code=None, sector_id=None, win_date=None, export_value=None,
                        confirm=False, agree_with_win=True, notify_date=None, response_date=None,
                        country=None, fin_year=2016, **kwargs):
        """ creates a dummy HVC `Win`, confirmed or unconfirmed """
        if hvc_code is None:
            hvc_code = FuzzyChoice(self.TEAM_1_HVCS).fuzz()

        return self._create_win(hvc_code=hvc_code, sector_id=sector_id, win_date=win_date,
                                export_value=export_value, confirm=confirm, agree_with_win=agree_with_win,
                                notify_date=notify_date, response_date=response_date, country=country,
                                fin_year=fin_year, **kwargs)

    def _create_non_hvc_win(self, sector_id=None, win_date=None, export_value=None, confirm=False,
                            agree_with_win=True, notify_date=None, response_date=None, country=None, fin_year=2016):
        """ creates a dummy non-HVC `Win` using Factory, can be confirmed or unconfirmed """
        return self._create_win(hvc_code=None, sector_id=sector_id, win_date=win_date, export_value=export_value,
                                confirm=confirm, agree_with_win=agree_with_win, notify_date=notify_date,
                                response_date=response_date, country=country, fin_year=fin_year)
