import datetime

from django.core.management import call_command
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from freezegun import freeze_time

from fixturedb.factories.win import create_win_factory
from mi.tests.base_test_case import MiApiViewsWithWinsBaseTestCase, MiApiViewsBaseTestCase


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17 + datetime.timedelta(weeks=5))
class GlobalWinsViewTestCase(MiApiViewsWithWinsBaseTestCase):
    """ Tests to test global win aggregate view `GlobalWinsView` """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.cen_campaign_url

    cen_campaign_url = reverse('mi:global_wins')
    CEN_17_HVCS = ["E017", "E018", "E019", "E020", "E219", "E220", "E221", "E222", ]
    export_value = 100000
    win_date_2017 = datetime.datetime(2017, 5, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)

    def test_global_number_no_wins_2016(self):
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_global_number_no_wins_2017(self):
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_hvc_confirmed_wins_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_hvc_confirmed_wins_2016_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_hvc_confirmed_wins_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_hvc_confirmed_wins_2017_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_hvc_confirmed_unconfirmed_wins_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value * 2)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], self.export_value * 2)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 2)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 2)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_non_hvc_confirmed_wins_2016(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)

    def test_glabal_non_hvc_confirmed_wins_2016_in_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_non_hvc_confirmed_wins_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)

    def test_glabal_non_hvc_confirmed_wins_2017_in_2016(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 0)

    def test_glabal_non_hvc_confirmed_unconfirmed_wins_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value * 2)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], self.export_value * 2)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], 0)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 1)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 2)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 2)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 0)

    def test_glabal_hvc_non_hvc_wins_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value * 2)
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value * 2)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], self.export_value)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], 2)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], 2)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 1)

    def test_glabal_multiple_wins_2017(self):
        for hvc_code in self.CEN_17_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                notify_date=self.win_date_2017,
                response_date=self.win_date_2017 + datetime.timedelta(days=1),
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        for hvc_code in self.CEN_17_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                notify_date=self.win_date_2017,
                response_date=self.win_date_2017 + datetime.timedelta(days=1),
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        for _ in range(10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        for _ in range(10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        no_of_cen_17_hvcs = len(self.CEN_17_HVCS)

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["total"]["value"]["confirmed"], self.export_value * (no_of_cen_17_hvcs + 10))
        self.assertEqual(api_response["wins"]["total"]["value"]["unconfirmed"], self.export_value * (no_of_cen_17_hvcs + 10))
        self.assertEqual(api_response["wins"]["total"]["value"]["total"], self.export_value * (no_of_cen_17_hvcs + 10) * 2)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["confirmed"], self.export_value * no_of_cen_17_hvcs)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["unconfirmed"], self.export_value * no_of_cen_17_hvcs)
        self.assertEqual(api_response["wins"]["hvc"]["value"]["total"], self.export_value * no_of_cen_17_hvcs * 2)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["confirmed"], self.export_value * 10)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["unconfirmed"], self.export_value * 10)
        self.assertEqual(api_response["wins"]["non_hvc"]["value"]["total"], self.export_value * 10 * 2)

        self.assertEqual(api_response["wins"]["total"]["number"]["confirmed"], no_of_cen_17_hvcs + 10)
        self.assertEqual(api_response["wins"]["total"]["number"]["unconfirmed"], no_of_cen_17_hvcs + 10)
        self.assertEqual(api_response["wins"]["total"]["number"]["total"], (no_of_cen_17_hvcs + 10) * 2)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["confirmed"], no_of_cen_17_hvcs)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["unconfirmed"], no_of_cen_17_hvcs)
        self.assertEqual(api_response["wins"]["hvc"]["number"]["total"], no_of_cen_17_hvcs * 2)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["confirmed"], 10)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["unconfirmed"], 10)
        self.assertEqual(api_response["wins"]["non_hvc"]["number"]["total"], 20)
