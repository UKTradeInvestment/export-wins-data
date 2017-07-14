import datetime

from django.utils.timezone import get_current_timezone
from factory.fuzzy import FuzzyChoice

from freezegun import freeze_time

from django.urls import reverse
from django.core.management import call_command

from fixturedb.factories.win import create_win_factory
from mi.factories import TargetFactory, SectorTeamFactory
from mi.models import FinancialYear, Country, HVCGroup
from mi.tests.base_test_case import MiApiViewsBaseTestCase, MiApiViewsWithWinsBaseTestCase
from wins.constants import SECTORS
from wins.factories import NotificationFactory
from wins.models import Notification


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

    def test_details_cen_hvc_win_unconfirmed_multi_notifications_no_duplicates(self):
        win = self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        # add couple of customer notifications
        notify_date = self.win_date_2017 + datetime.timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        notify_date = self.win_date_2017 + datetime.timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["totals"]["value"]["grand_total"], self.export_value)
        self.assertEqual(cen_response["wins"]["totals"]["number"]["grand_total"], 1)

@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class HVCTopHvcForMarketAndSectorTestCase(HVCBaseViewTestCase):
    TEST_CAMPAIGN_ID = "E017"
    TARGET_E017_17 = 30000000
    PRORATED_TARGET_17 = 2465760  # target based on the frozen date
    cen_campaign_url = reverse('mi:hvc_top_wins', kwargs={"campaign_id": "E017"})
    campaign_url_2016_only = reverse('mi:hvc_top_wins', kwargs={"campaign_id": "E177"})
    campaign_url_2017_only = reverse('mi:hvc_top_wins', kwargs={"campaign_id": "E218"})
    expected_response = {}
    SECTOR_58 = 58
    SECTOR_59 = 59
    SECTORS_DICT = dict(SECTORS)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.cen_campaign_url

    def test_top_hvc_with_no_wins(self):
        """ Top hvc wins will be empty if there are no wins """
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_with_conformed_non_hvc_wins(self):
        """ Top hvc wins will be empty when there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        self.url = self.get_url_for_year(2017)

        api_response = self._api_response_data
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_with_unconformed_non_hvc_wins(self):
        """ Top hvc wins will be empty when there are only unconfirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_with_unconfirmed_hvc_wins(self):
        """ Top hvc wins consider unconfirmed hvc wins as well """
        for _ in range(1, 10):
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
        self.assertTrue(len(api_response) > 0)

    def test_top_hvc_with_confirmed_hvc_wins(self):
        """ Top hvc wins consider confirmed hvc wins as well """
        for _ in range(1, 10):
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
        self.assertTrue(len(api_response) > 0)

    def test_top_hvc_with_confirmed_hvc_wins_one_sector_country(self):
        """ Number of Top hvc win items will only be 1 
        when there are confirmed hvc wins of one country/sector """
        for _ in range(1, 10):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                sector_id=self.SECTOR_58,
                country="HU",
                confirm=True,
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 1)

    def test_top_hvc_with_confirmed_hvc_wins_one_country(self):
        """
        Check number of hvc wins when there are more confirmed hvc
        wins of diff sector one country
        """
        for sector_id in range(1, 6):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country="HU",
                confirm=True,
                sector_id=sector_id,
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 5)

    def test_top_hvc_with_confirmed_hvc_wins_one_country_more_than_5(self):
        """
        Check number of hvc wins when there are more than 5 hvc wins
        of diff sector one country, show them all
        """
        for sector_id in range(10, 21):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country="HU",
                confirm=True,
                sector_id=sector_id,
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response) > 5)

    def test_top_hvc_with_confirmed_hvc_wins_one_sector_diff_country(self):
        """ Number of Top hvc wins will be more than 1 when there are 
        confirmed hvc wins of diff country one sector """
        for code in ['BS', 'GQ', 'VA', 'AQ', 'SA', 'EG', 'LU', 'ER', 'GA', 'MP']:
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country=code,
                sector_id=self.SECTOR_58,
                confirm=True,
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 10)

    def test_top_hvc_with_confirmed_hvc_wins_one_sector_one_country(self):
        """ Number of Top hvc wins will be 1 when there are 
        confirmed hvc wins of diff country one sector """
        for _ in range(1, 10):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country="HU",
                sector_id=self.SECTOR_58,
                confirm=True,
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 1)

    def test_values_top_hvc_top_win_with_confirmed_hvc_wins(self):
        """ Check top win is what is expected and its value, percentages are correct """
        expected_top_team = self.SECTOR_58
        for _ in range(0, 5):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country="HU",
                sector_id=expected_top_team,
                confirm=True,
                win_date=self.win_date_2017,
            )
        for _ in range(1, 10):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country="HU",
                confirm=True,
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response) > 5)
        top_item = api_response[0]
        self.assertEqual(top_item["sector"], self.SECTORS_DICT[expected_top_team])
        self.assertEqual(top_item["totalValue"], 100000 * 5)
        self.assertEqual(top_item["averageWinValue"], 100000)
        self.assertEqual(top_item["percentComplete"], 100)

    def test_top_hvc_compare_second_top_win_with_top(self):
        """ Check second top win with top, its value, percentages are correct """
        expected_top_team = self.SECTOR_58
        expected_second_team = self.SECTOR_59
        for _ in range(0, 5):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                country="HU",
                sector_id=expected_top_team,
                confirm=True,
                win_date=self.win_date_2017,
            )
        for _ in range(0, 4):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                sector_id=expected_second_team,
                confirm=True,
                country="HU",
                win_date=self.win_date_2017,
            )
        for _ in range(1, 10):
            self._create_hvc_win(
                hvc_code='E017',
                export_value=100000,
                confirm=True,
                country="HU",
                win_date=self.win_date_2017,
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response) >= 5)
        second_top_item = api_response[1]
        percent_complete = int((100000 * 4 * 100) / (100000 * 5))
        self.assertEqual(second_top_item["sector"], self.SECTORS_DICT[expected_second_team])
        self.assertEqual(second_top_item["totalValue"], 100000 * 4)
        self.assertEqual(second_top_item["averageWinValue"], 100000)
        self.assertEqual(second_top_item["percentComplete"], percent_complete)

    def test_top_hvc_check_items_percent_is_descending(self):
        """ Check percentage value is in descending order """
        for i in range(6, 1, -1):
            for _ in range(0, i):
                self._create_hvc_win(
                    hvc_code='E017',
                    export_value=100000,
                    sector_id=self.TEAM_1_SECTORS[i],
                    country="HU",
                    confirm=True,
                    win_date=self.win_date_2017,
                )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response) >= 5)
        self.assertTrue(api_response[0]["percentComplete"] >= api_response[1]["percentComplete"])
        self.assertTrue(api_response[1]["percentComplete"] >= api_response[2]["percentComplete"])
        self.assertTrue(api_response[2]["percentComplete"] >= api_response[3]["percentComplete"])
        self.assertTrue(api_response[3]["percentComplete"] >= api_response[4]["percentComplete"])

    def test_top_hvc_check_items_totalValue_is_descending(self):
        """ Check total value is in descending order """
        for i in range(6, 1, -1):
            for _ in range(0, i):
                self._create_hvc_win(
                    hvc_code='E017',
                    export_value=100000,
                    sector_id=self.TEAM_1_SECTORS[i],
                    country="HU",
                    confirm=True,
                    win_date=self.win_date_2017,
                )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response) >= 5)
        self.assertTrue(api_response[0]["totalValue"] >= api_response[1]["totalValue"])
        self.assertTrue(api_response[1]["totalValue"] >= api_response[2]["totalValue"])
        self.assertTrue(api_response[2]["totalValue"] >= api_response[3]["totalValue"])
        self.assertTrue(api_response[3]["totalValue"] >= api_response[4]["totalValue"])

    def test_top_hvc_check_items_averageWinValue_is_descending(self):
        """ Check average Win Value is in descending order """
        for i in range(6, 1, -1):
            for _ in range(0, i):
                self._create_hvc_win(
                    hvc_code='E017',
                    export_value=100000,
                    sector_id=self.TEAM_1_SECTORS[i],
                    country="HU",
                    confirm=True,
                    win_date=self.win_date_2017,
                )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response) >= 5)
        self.assertTrue(api_response[0]["averageWinValue"] >= api_response[1]["averageWinValue"])
        self.assertTrue(api_response[1]["averageWinValue"] >= api_response[2]["averageWinValue"])
        self.assertTrue(api_response[2]["averageWinValue"] >= api_response[3]["averageWinValue"])
        self.assertTrue(api_response[3]["averageWinValue"] >= api_response[4]["averageWinValue"])

    def test_top_hvc_with_hvc_wins_from_diff_campaign(self):
        for code in self.TEAM_1_HVCS:
            self._create_hvc_win(
                hvc_code=code,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_with_hvc_wins_from_2016(self):
        for _ in range(1, 10):
            self._create_hvc_win(
                hvc_code='E017',
                win_date=self.win_date_2016,
                response_date=self.win_date_2016,
                confirm=True,
                fin_year=2016,
                export_value=self.export_value,
                country='HU'
            )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_with_hvc_wins_from_2017_in_2016(self):
        for _ in range(1, 10):
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
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_hvc_win_from_2016_confirmed_in_2017_doesnt_appears_in_2016(self):
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
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 0)

    def test_top_hvc_hvc_win_from_2016_confirmed_in_2017_appears_in_2017(self):
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
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 1)


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class HVCWinTableTestCase(HVCBaseViewTestCase):
    TEST_CAMPAIGN_ID = "E002"
    cen_win_table_url = reverse('mi:hvc_win_table', kwargs={"campaign_id": "E002"})
    win_table_url_2016_only = reverse('mi:hvc_win_table', kwargs={"campaign_id": "E177"})
    win_table_url_2017_only = reverse('mi:hvc_win_table', kwargs={"campaign_id": "E218"})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.cen_win_table_url

    def test_2017_win_table_in_2016_404(self):
        self.view_base_url = self.win_table_url_2017_only
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_win_table_in_2017_404(self):
        self.view_base_url = self.win_table_url_2016_only
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_win_table_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "hvc": {
                "code": "E002",
                "name": "HVC: E002",
            },
            "wins": []
        }
        self.assertResponse()

    def test_win_table_json_2017_no_wins(self):
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "hvc": {
                "code": "E002",
                "name": "E00217",
            },
            "wins": []
        }
        self.assertResponse()

    def test_win_table_2017_one_confirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2017,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]) == 1)
        win_item = api_response["wins"][0]
        self.assertEqual(api_response["hvc"]["code"], "E002")
        self.assertEqual(api_response["hvc"]["name"], "E00217")
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_confirmed")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertTrue(win_item["credit"])

    def test_win_table_2017_one_unconfirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]) == 1)
        win_item = api_response["wins"][0]
        self.assertEqual(api_response["hvc"]["code"], "E002")
        self.assertEqual(api_response["hvc"]["name"], "E00217")
        self.assertIsNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "email_not_sent")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_unconfirmed_hvc_win_with_multiple_customer_notifications(self):
        win = self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )

        # add couple of customer notifications
        notify_date = self.win_date_2017 + datetime.timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        notify_date = self.win_date_2017 + datetime.timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]) == 1)

    def test_win_table_2017_one_unconfirmed_hvc_win_with_multiple_mixed_notifications(self):
        win = self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )

        # add a customer notification
        notify_date = self.win_date_2017 + datetime.timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        # add an officer notification
        notify_date = self.win_date_2017 + datetime.timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_OFFICER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]) == 1)

    def test_win_table_2017_one_confirmed_rejected_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2017,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]) == 1)
        win_item = api_response["wins"][0]
        self.assertEqual(api_response["hvc"]["code"], "E002")
        self.assertEqual(api_response["hvc"]["name"], "E00217")
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_rejected")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2017(self):
        self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]) == 1)
        win_item = api_response["wins"][0]
        self.assertEqual(api_response["hvc"]["code"], "E002")
        self.assertEqual(api_response["hvc"]["name"], "E00217")
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_rejected")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2016_no_result(self):
        self._create_hvc_win(
            hvc_code='E002',
            win_date=self.win_date_2016,
            response_date=self.win_date_2016,
            confirm=True,
            agree_with_win=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            'wins': [],
            'hvc': {
                'code': 'E002',
                'name': 'E00217'
            }
        }
        self.assertResponse()

    def test_win_table_2017_confirmed_non_hvc_empty_result(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            'wins': [],
            'hvc':
                {
                    'code': 'E002',
                    'name': 'E00217'
                }
        }
        self.assertResponse()

    def test_win_table_2017_unconfirmed_non_hvc_empty_result(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            'wins': [],
            'hvc':
                {
                    'code': 'E002',
                    'name': 'E00217'
                }
        }
        self.assertResponse()


class TestGlobalHVCList(MiApiViewsBaseTestCase):

    url = reverse('mi:global_hvcs') + "?year=2017"

    def create_global_hvc(self):
        fy2017 = FinancialYear.objects.get(id=2017)
        sector_team = SectorTeamFactory.create()
        hvc_group = FuzzyChoice(HVCGroup.objects.all())

        target = TargetFactory.create(campaign_id='E225', financial_year=fy2017, hvc_group=hvc_group, sector_team=sector_team)
        target.country.add(Country.objects.get(country='XG'))
        return target

    def test_2017_returns_1_hvcs(self):
        self.create_global_hvc()
        data = self._api_response_data

        self.assertEqual(
            data,
            [{
                "code": "E225",
                "name": "HVC: E225"
            }]
        )

    def test_2016_returns_0_hvcs(self):
        self.create_global_hvc()
        self.url = reverse('mi:global_hvcs') + "?year=2016"
        data = self._api_response_data

        self.assertEqual(
            data,
            []
        )

    def test_2017_returns_0_hvs_if_none_exist(self):
        data = self._api_response_data

        self.assertEqual(
            data,
            []
        )
