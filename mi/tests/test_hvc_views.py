import datetime

from django.utils.timezone import get_current_timezone

from freezegun import freeze_time

from django.urls import reverse
from django.core.management import call_command

from fixturedb.factories.win import create_win_factory
from mi.tests.base_test_case import MiApiViewsBaseTestCase, MiApiViewsWithWinsBaseTestCase


class HVCBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):
    view_base_url = reverse('mi:hvc_campaign_detail', kwargs={"campaign_id": "E017"})
    export_value = 100000
    win_date_2017 = datetime.datetime(2017, 5, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())
    fy_2016_last_date = datetime.datetime(2017, 3, 31, tzinfo=get_current_timezone())

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class HVCDetailsTestCase(HVCBaseViewTestCase):
    TEST_CAMPAIGN_ID = "E017"
    TARGET_E017_17 = 30000000
    PRORATED_TARGET_17 = 2465760  # target based on the frozen date

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.cen_campaign_url

    cen_campaign_url = reverse('mi:hvc_campaign_detail', kwargs={"campaign_id": "E017"})
    campaign_url_2016_only = reverse('mi:hvc_campaign_detail', kwargs={"campaign_id": "E177"})
    campaign_url_2017_only = reverse('mi:hvc_campaign_detail', kwargs={"campaign_id": "E218"})

    def test_2017_campaign_in_2016_404(self):
        self.view_base_url = self.campaign_url_2017_only
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_campaign_in_2017_404(self):
        self.view_base_url = self.campaign_url_2016_only
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_details_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "wins": {
                "totals": {
                    "value": {
                        "grand_total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "number": {
                        "grand_total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                },
                "progress": {
                    "status": "red",
                    "unconfirmed_percent": 0,
                    "confirmed_percent": 0
                }
            },
            "name": "HVC: E017",
            "campaign_id": "E017",
            "hvcs": {
                "campaigns": [
                    "HVC: E017",
                ],
                "target": self.CAMPAIGN_TARGET
            },
            "avg_time_to_confirm": 0.0
        }
        self.assertResponse()

    def test_details_no_wins_2016(self):
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(api_response["wins"]["totals"]["number"]["grand_total"], 0)

        self.assertEqual(api_response["wins"]["progress"]["status"], "red")
        self.assertEqual(api_response["wins"]["progress"]["unconfirmed_percent"], 0)
        self.assertEqual(api_response["wins"]["progress"]["confirmed_percent"], 0)

    def test_details_no_wins_2017(self):
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(api_response["wins"]["totals"]["number"]["grand_total"], 0)

        self.assertEqual(api_response["wins"]["progress"]["status"], "red")
        self.assertEqual(api_response["wins"]["progress"]["unconfirmed_percent"], 0)
        self.assertEqual(api_response["wins"]["progress"]["confirmed_percent"], 0)

    def test_details_e017_hvc_win_for_2017_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)

    def test_details_cen_hvc_win_for_2017_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

    def test_details_cen_hvc_win_for_2016_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)

    def test_details_cen_hvc_win_for_2016_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

    def test_details_cen_hvc_win_confirmed_in_2016_appears_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)

    def test_details_cen_hvc_win_confirmed_in_2016_doesnt_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

    def test_details_cen_hvc_win_from_2016_confirmed_in_2017_doesnt_appears_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

    def test_details_cen_hvc_win_from_2016_confirmed_in_2017_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)

    def test_details_hvc_win_from_other_region_but_cen_country_doesnt_appear_in_cen(self):
        self._create_hvc_win(
            hvc_code='E016',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

    def test_details_hvc_win_from_other_region_other_country_doesnt_appear_in_cen(self):
        self._create_hvc_win(
            hvc_code='E016',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='CA'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

    def test_details_cen_hvc_win_unconfirmed_in_2016_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)

    def test_details_cen_hvc_win_unconfirmed_in_2017_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 0)

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)
