import json

from django.utils.datetime_safe import datetime
from django.utils.timezone import get_current_timezone
from factory.fuzzy import FuzzyChoice

from fixturedb.factories.win import create_win_factory
from sso.tests import BaseSSOTestCase
from users.factories import UserFactory
from wins.factories import HVCFactory
from wins.models import Win


class MiApiViewsBaseTestCase(BaseSSOTestCase):
    maxDiff = None
    fin_start_date = datetime(2016, 4, 1, tzinfo=get_current_timezone())
    frozen_date = datetime(2016, 11, 1, tzinfo=get_current_timezone())
    fin_end_date = datetime(2017, 3, 31, tzinfo=get_current_timezone())
    frozen_date_17 = datetime(2017, 5, 1, tzinfo=get_current_timezone())

    TEAM_1_HVCS = ['E006', 'E019', 'E031', 'E072', 'E095', 'E115', 'E128', 'E160', 'E167', 'E191']
    TEAM_15_HVCS = ['E025', 'E026', 'E051', 'E058', 'E066', 'E067', 'E083', 'E132', 'E149',
                    'E156', 'E158', 'E174', 'E186', 'E187', 'E219', 'E229']
    TEAM_1_SECTORS = [60, 61, 62, 63, 64, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159,
                      160, 161, 162, 163, 164, 165, 166, 167, 168, 169]
    TEAM_15_SECTORS = [72, 73, 74, 75, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104,
                        105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 183,
                        184, 185, 205, 207, 208, 209, 210, 211, 242, 256]
    SAMPLE_COUNTRIES = ['CA', 'BS', 'GQ', 'VA', 'AQ', 'SA', 'EG', 'LU', 'ER', 'GA', 'MP']
    CAMPAIGN_TARGET = 10000000

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = UserFactory.create()
        cls.user.save()
        # needed to get names of HVCs, have to do again because factory
        # remembers other tests, even if flushed from DB
        for i in range(255):
            HVCFactory.create(
                campaign_id='E%03d' % (i + 1),
                financial_year=16,
            )

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

    def _create_win(self, hvc_code, agree_with_win, sector_id=None, win_date=None, export_value=None,
                    confirm=False, notify_date=None, response_date=None, country=None,
                    fin_year=2016):
        """ generic function creating `Win`
        :rtype: `Win`
        """
        win = self._win_factory_function(
            hvc_code,
            sector_id=sector_id,
            win_date=win_date,
            export_value=export_value,
            confirm=confirm,
            notify_date=notify_date,
            response_date=response_date,
            country=country,
            fin_year=fin_year
        )
        return win

    def _create_hvc_win(self, hvc_code=None, sector_id=None, win_date=None, export_value=None,
                        confirm=False, agree_with_win=True, notify_date=None, response_date=None,
                        country=None, fin_year=2016):
        """ creates a dummy HVC `Win`, confirmed or unconfirmed """
        if hvc_code is None:
            hvc_code = FuzzyChoice(self.TEAM_1_HVCS).fuzz()

        return self._create_win(hvc_code=hvc_code, sector_id=sector_id, win_date=win_date,
                                export_value=export_value, confirm=confirm, agree_with_win=agree_with_win,
                                notify_date=notify_date, response_date=response_date, country=country,
                                fin_year=fin_year)

    def _create_non_hvc_win(self, sector_id=None, win_date=None, export_value=None, confirm=False,
                            agree_with_win=True, notify_date=None, response_date=None, country=None, fin_year=2016):
        """ creates a dummy non-HVC `Win` using Factory, can be confirmed or unconfirmed """
        return self._create_win(hvc_code=None, sector_id=sector_id, win_date=win_date, export_value=export_value,
                                confirm=confirm, agree_with_win=agree_with_win, notify_date=notify_date,
                                response_date=response_date, country=country, fin_year=fin_year)
