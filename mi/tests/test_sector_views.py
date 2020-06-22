import datetime

from django.core.management import call_command
from django.utils.timezone import get_current_timezone
from freezegun import freeze_time

import json
from dateutil.relativedelta import relativedelta

from django.urls import reverse
from factory.fuzzy import FuzzyDate
from jmespath import search as s

from fixturedb.factories.win import create_win_factory
from mi.models import Target, TargetCountry
from mi.tests.base_test_case import MiApiViewsBaseTestCase, MiApiViewsWithWinsBaseTestCase
from mi.tests.utils import GenericTopNonHvcWinsTestMixin, GenericWinTableTestMixin
from mi.utils import sort_campaigns_by
from wins.constants import SECTORS
from wins.models import HVC


class SectorTeamBaseTestCase(MiApiViewsWithWinsBaseTestCase):
    frozen_date_17 = datetime.datetime(2017, 5, 28, tzinfo=get_current_timezone())

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(self.user, sector_choices=self.TEAM_1_SECTORS)

    def _hvc_charcode(self, hvc_code, fin_year):
        charcode = hvc_code + str(fin_year)[-2:]
        return charcode

    def _team_data(self, teams_list, team_id=1):
        """ returns specific team's data dict out of overview response list """
        team_data = next((team_item for team_item in teams_list if team_item["id"] == team_id), None)
        self.assertIsNotNone(team_data)
        return team_data

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamListTestCase(SectorTeamBaseTestCase):
    """
    Tests covering SectorTeam overview and detail API endpoints
    """

    url = reverse("mi:sector_teams") + "?year=2016"

    def test_sector_teams_list(self):
        """ test `SectorTeam` list API """

        self.expected_response = sorted([
            {
                "id": 1,
                "name": "Financial & Professional Services",
                "hvc_groups": [
                    {
                        "id": 16,
                        "name": "Financial Services"
                    },
                    {
                        "id": 26,
                        "name": "Professional Services"
                    }
                ]
            },
            {
                "id": 2,
                "name": "Education",
                "hvc_groups": [
                    {
                        "id": 11,
                        "name": "Education"
                    }
                ]
            },
            {
                "id": 3,
                "name": "Technology",
                "hvc_groups": [
                    {
                        "id": 10,
                        "name": "Digital Economy"
                    }
                ]
            },
            {
                "id": 4,
                "name": "Food & Drink",
                "hvc_groups": [
                    {
                        "id": 17,
                        "name": "Food & Drink"
                    }
                ]
            },
            {
                "id": 5,
                "name": "Aerospace",
                "hvc_groups": [
                    {
                        "id": 3,
                        "name": "Aerospace"
                    }
                ]
            },
            {
                "id": 6,
                "name": "Infrastructure",
                "hvc_groups": [
                    {
                        "id": 19,
                        "name": "Infrastructure - Aid Funded Business"
                    },
                    {
                        "id": 20,
                        "name": "Infrastructure - Airports"
                    },
                    {
                        "id": 21,
                        "name": "Infrastructure - Construction"
                    },
                    {
                        "id": 22,
                        "name": "Infrastructure - Mining"
                    },
                    {
                        "id": 23,
                        "name": "Infrastructure - Rail"
                    },
                    {
                        "id": 24,
                        "name": "Infrastructure - Water"
                    }
                ]
            },
            {
                "id": 7,
                "name": "Energy",
                "hvc_groups": [
                    {
                        "id": 12,
                        "name": "Energy - Nuclear"
                    },
                    {
                        "id": 13,
                        "name": "Energy - Offshore Wind"
                    },
                    {
                        "id": 14,
                        "name": "Energy - Oil & Gas"
                    },
                    {
                        "id": 15,
                        "name": "Energy - Renewables"
                    }
                ]
            },
            {
                "id": 8,
                "name": "Life Sciences",
                "hvc_groups": [
                    {
                        "id": 25,
                        "name": "Life Sciences"
                    }
                ]
            },
            {
                "id": 9,
                "name": "Advanced Manufacturing",
                "hvc_groups": [
                    {
                        "id": 1,
                        "name": "Advanced Manufacturing"
                    },
                    {
                        "id": 2,
                        "name": "Advanced Manufacturing - Marine"
                    }
                ]
            },
            {
                "id": 10,
                "name": "Consumer & Creative",
                "hvc_groups": [
                    {
                        "id": 7,
                        "name": "Consumer Goods & Retail"
                    },
                    {
                        "id": 8,
                        "name": "Creative Industries"
                    },
                    {
                        "id": 27,
                        "name": "Sports Economy"
                    }
                ]
            },
            {
                "id": 11,
                "name": "Automotive",
                "hvc_groups": [
                    {
                        "id": 4,
                        "name": "Automotive"
                    }
                ]
            },
            {
                "id": 12,
                "name": "Healthcare",
                "hvc_groups": [
                    {
                        "id": 18,
                        "name": "Healthcare"
                    }
                ]
            },
            {
                "id": 13,
                "name": "Bio-economy",
                "hvc_groups": [
                    {
                        "id": 5,
                        "name": "Bio-economy - Agritech"
                    },
                    {
                        "id": 6,
                        "name": "Bio-economy - Chemicals"
                    }
                ]
            },
            {
                "id": 14,
                "name": "Defence & Security",
                "hvc_groups": [
                    {
                        "id": 9,
                        "name": "Defence"
                    },
                    {
                        "id": 28,
                        "name": "Strategic Campaigns"
                    }
                ]
            }
        ], key=lambda x: (x["name"]))
        self.assertResponse()


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamCampaignViewsTestCase(SectorTeamBaseTestCase):
    """
    Tests covering SectorTeam Campaigns API endpoint
    """
    expected_response = {}
    TEST_CAMPAIGN_ID = "E006"
    TEST_CHARCODE = TEST_CAMPAIGN_ID + "16"
    url = reverse("mi:sector_team_campaigns", kwargs={"team_id": 1}) + "?year=2016"

    def _campaign_data(self, campaign_list, hvc_code):
        """ returns specific campaign's data out of Campaigns list """
        campaign_data = next(
            (campaign_item for campaign_item in campaign_list if campaign_item["campaign_id"] == hvc_code),
            None
        )
        self.assertIsNotNone(campaign_data)
        return campaign_data

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self.expected_response = {
            "campaigns": [],
            "name": "Financial & Professional Services",
            "hvcs": {
                "campaigns": [
                    "HVC: E006",
                    "HVC: E019",
                    "HVC: E031",
                    "HVC: E072",
                    "HVC: E095",
                    "HVC: E115",
                    "HVC: E128",
                    "HVC: E160",
                    "HVC: E167",
                    "HVC: E191"
                ],
                "target": self.CAMPAIGN_TARGET * len(self.TEAM_1_HVCS)
            },
            "avg_time_to_confirm": 0.0
        }

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_cross_fy_wins_in_team_15_with_change(self):
        """
        This is to test a win that was created in previous FY and confirmed in current FY
        for team 15 who's name was changed across FYs.
        """
        from django.core.management import call_command
        call_command('create_missing_hvcs', verbose=False)

        self._create_hvc_win(hvc_code="E083", confirm=True,
                             export_value=10000000,
                             win_date=datetime.datetime(2017, 3, 25),
                             notify_date=datetime.datetime(2017, 3, 25),
                             response_date=datetime.datetime(2017, 4, 5),
                             fin_year=2016)
        team_15_campaign_url = reverse("mi:sector_team_campaigns", kwargs={"team_id": 15}) + "?year=2017"
        api_response = self._get_api_response(team_15_campaign_url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        hvc_data = next((item for item in response_decoded["campaigns"] if item["campaign_id"] == "E083"), None)
        self.assertIsNotNone(hvc_data)
        total = hvc_data["totals"]["hvc"]["value"]["confirmed"]
        self.assertEqual(10000000, total)

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_cross_fy_wins_in_team_1_with_change(self):
        """
        This is to test a win that was created in previous FY and confirmed in current FY
        for a team 1 who's name hasn't changed across FYs.
        """
        from django.core.management import call_command
        call_command('create_missing_hvcs', verbose=False)

        self._create_hvc_win(hvc_code='E006', confirm=True,
                             export_value=10000000,
                             win_date=datetime.datetime(2017, 3, 25),
                             notify_date=datetime.datetime(2017, 3, 25),
                             response_date=datetime.datetime(2017, 4, 5),
                             fin_year=2016)
        team_1_2017_campaign_url = reverse("mi:sector_team_campaigns", kwargs={"team_id": 1}) + "?year=2017"
        api_response = self._get_api_response(team_1_2017_campaign_url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        hvc_data = next((item for item in response_decoded["campaigns"] if item["campaign_id"] == "E006"), None)
        self.assertIsNotNone(hvc_data)
        total = hvc_data["totals"]["hvc"]["value"]["confirmed"]
        self.assertEqual(10000000, total)

    def test_sector_team_campaigns_1_wins_for_all_hvcs(self):
        """ Campaigns api for team 1, with wins for all HVCs"""
        campaigns = []
        count = len(self.TEAM_1_HVCS)
        for hvc_code in self.TEAM_1_HVCS:
            # add export value such that we get response in a specific order
            export_value = count * 100000
            percent = (export_value * 100) / self.CAMPAIGN_TARGET
            self._create_hvc_win(hvc_code=hvc_code, confirm=True, export_value=export_value,
                                 notify_date=datetime.datetime(2016, 5, 2), response_date=datetime.datetime(2016, 5, 6))
            hvc = HVC.objects.get(campaign_id=hvc_code, financial_year=16)

            campaigns.append({
                "campaign": hvc.campaign,
                "campaign_id": hvc.campaign_id,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": 0,
                            "confirmed": export_value,
                            "total": export_value
                        },
                        "number": {
                            "unconfirmed": 0,
                            "confirmed": 1,
                            "total": 1
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": 0.0,
                        "confirmed_percent": percent,
                        "status": "red"
                    },
                    "target": self.CAMPAIGN_TARGET
                }
            })

        self.expected_response["campaigns"] = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        self.expected_response["avg_time_to_confirm"] = 4.0

        self.assertResponse()

    def test_sector_team_campaigns_1_wins_for_all_hvcs_unconfirmed(self):
        """ Campaigns api for team 1, with wins for all HVCs"""
        campaigns = []
        count = len(self.TEAM_1_HVCS)
        for hvc_code in self.TEAM_1_HVCS:
            # add export value such that we get response in a specific order
            export_value = count * 100000
            percent = (export_value * 100) / self.CAMPAIGN_TARGET
            self._create_hvc_win(hvc_code=hvc_code, export_value=export_value)
            count -= 1
            hvc = HVC.objects.get(campaign_id=hvc_code, financial_year=16)

            campaigns.append({
                "campaign": hvc.campaign,
                "campaign_id": hvc.campaign_id,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": export_value,
                            "confirmed": 0,
                            "total": export_value
                        },
                        "number": {
                            "unconfirmed": 1,
                            "confirmed": 0,
                            "total": 1
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": percent,
                        "confirmed_percent": 0.0,
                        "status": "red"
                    },
                    "target": self.CAMPAIGN_TARGET
                }
            })

        self.expected_response["campaigns"] = sorted(campaigns, key=lambda c: (
            c["totals"]["progress"]["confirmed_percent"],
            c["totals"]["progress"]["unconfirmed_percent"],
            c["totals"]["target"]), reverse=True)

        self.assertResponse()

    def test_total_target_with_no_wins(self):
        """ Test that there is no effect on Total Target when there are no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        expected_total = len(self.TEAM_1_HVCS) * self.CAMPAIGN_TARGET
        response_total = response_decoded["hvcs"]["target"]
        self.assertEqual(expected_total, response_total)

    def test_total_target_with_unconfirmed_wins(self):
        """ Unconfirmed wins will not have effect on Total Target """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        expected_total = len(self.TEAM_1_HVCS) * self.CAMPAIGN_TARGET
        response_total = response_decoded["hvcs"]["target"]
        self.assertEqual(expected_total, response_total)

    def test_total_target_with_confirmed_wins(self):
        """ Any number of confirmed wins will not have effect on Total Target """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        expected_total = len(self.TEAM_1_HVCS) * self.CAMPAIGN_TARGET
        response_total = response_decoded["hvcs"]["target"]
        self.assertEqual(expected_total, response_total)

    def test_avg_time_to_confirm_no_wins(self):
        """ Average time to confirm will be zero when no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        expected_avg_time = 0.0
        response_avg_time = response_decoded["avg_time_to_confirm"]
        self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_unconfirmed_wins(self):
        """ Average time to confirm will be zero, if there are no confirmed wins """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        expected_avg_time = 0.0
        response_avg_time = response_decoded["avg_time_to_confirm"]
        self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_nextday(self):
        """ Test average time to confirm when all wins confirmed in one day """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        expected_avg_time = 1.0
        response_avg_time = response_decoded["avg_time_to_confirm"]
        self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_randomly(self):
        """
        Average time to confirm should be more than one,
        when wins took more than one day to be confirmed
        """
        for hvc_code in self.TEAM_1_HVCS:
            response_date = FuzzyDate(datetime.datetime(2016, 5, 27), datetime.datetime(2016, 5, 31)).evaluate(2, None,
                                                                                                               False)
            self._create_hvc_win(hvc_code=hvc_code, confirm=True, response_date=response_date)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        response_avg_time = response_decoded["avg_time_to_confirm"]
        self.assertTrue(response_avg_time > 1.0)

    def test_campaigns_count_no_wins(self):
        """ Make sure number of campaigns returned have no effect when there are no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(self.TEAM_1_HVCS))

    def test_campaigns_count_unconfirmed_wins(self):
        """ unconfirmed wins shouldn't have any effect on number of campaigns """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(self.TEAM_1_HVCS))

    def test_campaigns_count_confirmed_wins(self):
        """ confirmed HVC wins shouldn't have any effect on number of campaigns """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(self.TEAM_1_HVCS))

    def test_campaigns_count_unconfirmed_nonhvc_wins(self):
        """ unconfirmed non-hvc wins shouldn't have any effect on number of campaigns """
        for _ in self.TEAM_1_HVCS:
            self._create_non_hvc_win(confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(self.TEAM_1_HVCS))

    def test_campaigns_count_confirmed_nonhvc_wins(self):
        """ unconfirmed non-hvc wins shouldn't have any effect on number of campaigns """
        for _ in self.TEAM_1_HVCS:
            self._create_non_hvc_win(confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(self.TEAM_1_HVCS))

    def test_campaign_progress_colour_no_wins(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "red")

    def test_campaign_progress_colour_unconfirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are no confirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "red")

    def test_campaign_progress_colour_confirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are not enough confirmed wins """
        self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "red")

    def test_campaign_progress_colour_nonhvc_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are only non-hvc wins """
        for _ in range(1, 11):
            self._create_non_hvc_win(export_value=100000)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "red")

    def test_campaign_progress_colour_nonhvc_confirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "red")

    def test_campaign_progress_colour_confirmed_wins_amber(self):
        """
        Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        for _ in range(1, 3):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=1000000, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "amber")

    def test_campaign_progress_confirmed_wins_50_green(self):
        """ Progress colour should be green if there are enough win to take runrate past 45% """
        for _ in range(1, 5):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=1000000, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "green")

    def test_campaign_progress_confirmed_wins_45_green(self):
        """ Boundary Testing for Green:
        Progress colour should be green if there are enough win to take runrate past 45% """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=263900, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "green")

    def test_campaign_progress_confirmed_wins_44_amber(self):
        """
        Boundary testing for Amber: Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=263777, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "amber")

    def test_campaign_progress_confirmed_wins_25_amber(self):
        """
        Boundary testing for Amber: Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=146700, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "amber")

    def test_campaign_progress_confirmed_wins_24_red(self):
        """ Boundary testing for red: Anything less than 25% runrate of progress should be Red """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=146516.5, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["status"], "red")

    def test_campaign_progress_percent_no_wins(self):
        """ Progress percentage will be 0, if there are no confirmed HVC wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["confirmed_percent"], 0.0)
        self.assertEqual(campaign_data["totals"]["progress"]["unconfirmed_percent"], 0.0)

    def test_campaign_progress_percent_unconfirmed_wins(self):
        """ Progress percentage will be 0, if there are no confirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["confirmed_percent"], 0.0)
        self.assertEqual(campaign_data["totals"]["progress"]["unconfirmed_percent"], 10.0)

    def test_campaign_progress_percent_confirmed_wins_1(self):
        """ Test simple progress percent """
        self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["confirmed_percent"], 1.0)
        self.assertEqual(campaign_data["totals"]["progress"]["unconfirmed_percent"], 0.0)

    def test_campaign_progress_percent_nonhvc_wins(self):
        """ Non hvc wins shouldn't effect progress percent """
        for _ in range(1, 11):
            self._create_non_hvc_win(export_value=100000)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["confirmed_percent"], 0.0)
        self.assertEqual(campaign_data["totals"]["progress"]["unconfirmed_percent"], 0.0)

    def test_campaign_progress_percent_nonhvc_confirmed_wins(self):
        """ Non hvc confirmed wins shouldn't effect progress percent """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["confirmed_percent"], 0.0)
        self.assertEqual(campaign_data["totals"]["progress"]["unconfirmed_percent"], 0.0)

    def test_campaign_progress_percent_confirmed_wins_20(self):
        """ Check 20% progress percent """
        for _ in range(1, 3):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=1000000, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["progress"]["confirmed_percent"], 20.0)
        self.assertEqual(campaign_data["totals"]["progress"]["unconfirmed_percent"], 0.0)

    def test_campaign_hvc_number_no_wins(self):
        """ HVC number shouldn't be affected when there are no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["total"], 0)

    def test_campaign_hvc_number_only_nonhvc_wins(self):
        """ HVC number shouldn't be affected when there are only non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["total"], 0)

    def test_campaign_hvc_number_only_nonhvc_confirmed_wins(self):
        """ HVC number shouldn't be affected when there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["total"], 0)

    def test_campaign_hvc_number_unconfirmed_wins(self):
        """ Check HVC number with unconfirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["unconfirmed"], 10)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["total"], 10)

    def test_campaign_hvc_number_confirmed_wins(self):
        """ Check HVC number with confirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["confirmed"], 10)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["total"], 10)

    def test_campaign_hvc_number_mixed_wins(self):
        """ Check HVC numbers with both confirmed and unconfirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=False)
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["confirmed"], 10)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["unconfirmed"], 10)
        self.assertEqual(campaign_data["totals"]["hvc"]["number"]["total"], 20)

    def test_campaign_hvc_value_no_wins(self):
        """ HVC value will be 0 with there are no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["total"], 0)

    def test_campaign_hvc_value_only_nonhvc_wins(self):
        """ HVC value will be 0 there are only unconfirmed non-HVC wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["total"], 0)

    def test_campaign_hvc_value_only_nonhvc_confirmed_wins(self):
        """ HVC value will be 0 when there are only confirmed non-HVC wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["total"], 0)

    def test_campaign_hvc_value_unconfirmed_wins(self):
        """ Check HVC value when there are unconfirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=False)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["unconfirmed"], 1000000)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["total"], 1000000)

    def test_campaign_hvc_value_confirmed_wins(self):
        """ Check HVC value when there are confirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["confirmed"], 1000000)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["total"], 1000000)

    def test_campaign_hvc_value_mixed_wins(self):
        """ Check HVC value when there are both confirmed and unconfirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=False)
        for _ in range(1, 11):
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=100000, confirm=True)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        campaign_data = self._campaign_data(response_decoded["campaigns"], self.TEST_CAMPAIGN_ID)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["confirmed"], 1000000)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["unconfirmed"], 1000000)
        self.assertEqual(campaign_data["totals"]["hvc"]["value"]["total"], 2000000)

    @freeze_time(SectorTeamBaseTestCase.frozen_date_17)
    def test_campaign_hvc_win_added_previous_fy_but_no_hvc_this_year_should_be_non_hvc(self):
        self.url = reverse("mi:sector_team_campaigns", kwargs={"team_id": 1}) + "?year=2017"
        t = Target.objects.get(campaign_id=self.TEST_CAMPAIGN_ID, financial_year_id=2017)

        w1 = self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            export_value=100000,
            response_date=self.frozen_date_17 + relativedelta(weeks=-1),
            win_date=self.frozen_date_17 + relativedelta(months=-9),
            fin_year=2016,
            agree_with_win=True,
            confirm=True
        )

        # if there is a target for 2017
        data = self._api_response_data
        self.assertEqual(
            s('sum(campaigns[].totals[].hvc.value.confirmed)', data),
            w1.total_expected_export_value
        )

        TargetCountry.objects.filter(target=t).delete()
        t.delete()
        data = self._api_response_data
        self.assertEqual(
            s('sum(campaigns[].totals[].hvc.value.confirmed)', data),
            0
        )

@freeze_time(SectorTeamBaseTestCase.frozen_date_17)
class SectorOverviewTestCase(SectorTeamBaseTestCase):
    url = reverse('mi:sector_teams_overview') + "?year=2017"
    TEST_CAMPAIGN_ID = 'E006'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def test_overview_closed_hvc_is_treated_as_non_hvc(self):
        hvc = HVC.objects.get(campaign_id=self.TEST_CAMPAIGN_ID, financial_year=17)

        w1 = self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            export_value=100000,
            response_date=self.frozen_date_17 + relativedelta(weeks=-1),
            win_date=self.frozen_date_17 + relativedelta(months=-9),
            fin_year=2016,
            agree_with_win=True,
            confirm=True
        )

        # if there is a hvc for 2017
        data = self._api_response_data
        self.assertEqual(
            s("[?name == 'Financial & Professional Services'].values.hvc.current.confirmed | [0]", data),
            w1.total_expected_export_value
        )
        self.assertEqual(
            s("[?name == 'Financial & Professional Services'].values.non_hvc.current.confirmed | [0]", data),
            0
        )

        hvc.delete()
        data = self._api_response_data
        self.assertEqual(
            s("[?name == 'Financial & Professional Services'].values.hvc.current.confirmed | [0]", data),
            0
        )
        self.assertEqual(
            s("[?name == 'Financial & Professional Services'].values.non_hvc.current.confirmed | [0]", data),
            w1.total_expected_export_value
        )


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamTopNonHvcTestCase(SectorTeamBaseTestCase, GenericTopNonHvcWinsTestMixin):
    expected_response = {}
    fin_years = [2016]
    export_value = 9999
    view_base_url = reverse("mi:sector_team_top_non_hvc", kwargs={"team_id": 1})
    url = view_base_url + "?year=2016"
    win_date_2016 = datetime.datetime(2016, 4, 23)

    TEST_COUNTRY_CODE = 'CI'

    SECTORS_DICT = dict(SECTORS)

    def test_top_non_hvc_with_no_wins(self):
        """ Top non-hvc wins will be empty if there are no wins """
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 0)

    def test_top_non_hvc_with_conformed_hvc_wins(self):
        """ Top non-hvc wins will be empty when there are only unconfirmed hvc wins """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 0)

    def test_top_non_hvc_with_unconformed_hvc_wins(self):
        """ Top non-hvc wins will be empty when there are only unconfirmed hvc wins """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 0)

    def test_top_non_hvc_with_unconfirmed_non_hvc_wins(self):
        """ Top non-hvc wins consider unconfirmed non-hvc wins as well """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 5)

    def test_top_non_hvc_with_confirmed_non_hvc_wins_one_sector_country(self):
        """ Number of Top non-hvc wins will be 1 when there are confirmed non-hvc wins of one country/sector """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                export_value=100000,
                sector_id=self.FIRST_TEAM_1_SECTOR,
                country="CA", confirm=True
            )

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 1)

    def test_top_non_hvc_with_confirmed_non_hvc_wins_one_country(self):
        """
        Number of Top non-hvc wins is limited to 5 even when there are
        more confirmed non-hvc wins of diff sector one country
        """
        for _ in range(1, 10):
            self._create_non_hvc_win(export_value=100000, country="CA", confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 5)

    def test_top_non_hvc_with_confirmed_non_hvc_wins_one_sector(self):
        """ Number of Top non-hvc wins will be 1 when there are confirmed non-hvc wins of diff country one sector """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                export_value=100000,
                sector_id=self.FIRST_TEAM_1_SECTOR,
                confirm=True
            )

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 1)

    def test_top_non_hvc_top_win_with_confirmed_non_hvc_wins(self):
        """ Check top win is what is expected and its value, percentages are correct """
        expected_top_team = self.FIRST_TEAM_1_SECTOR
        for _ in range(0, 5):
            self._create_non_hvc_win(export_value=100000, sector_id=expected_top_team, confirm=True)
        for sector_id in self.SECTORS_NOT_IN_EITHER_TEAM:
            self._create_non_hvc_win(export_value=100000, confirm=True, sector_id=sector_id)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 1)
        top_item = response_decoded[0]
        self.assertEqual(top_item["sector"], self.SECTORS_DICT[expected_top_team], msg=top_item)
        self.assertEqual(top_item["totalValue"], 100000 * 5, msg=top_item)
        self.assertEqual(top_item["averageWinValue"], 100000)
        self.assertEqual(top_item["percentComplete"], 100)

    def test_top_non_hvc_compare_second_top_win_with_top(self):
        """ Check second top win with top, its value, percentages are correct """
        expected_top_team = self.FIRST_TEAM_1_SECTOR
        expected_second_team = self.SECOND_TEAM_1_SECTOR
        for _ in range(0, 5):
            self._create_non_hvc_win(export_value=100000, sector_id=expected_top_team, confirm=True)
        for _ in range(0, 4):
            self._create_non_hvc_win(export_value=100000, sector_id=expected_second_team, confirm=True)
        for sector_id in self.SECTORS_NOT_IN_EITHER_TEAM:
            self._create_non_hvc_win(export_value=100000, confirm=True, sector_id=sector_id)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 2)
        second_top_item = response_decoded[1]
        percent_complete = int((100000 * 4 * 100) / (100000 * 5))
        self.assertEqual(second_top_item["sector"], self.SECTORS_DICT[expected_second_team], msg=second_top_item)
        self.assertEqual(second_top_item["totalValue"], 100000 * 4, msg=second_top_item)
        self.assertEqual(second_top_item["averageWinValue"], 100000)
        self.assertEqual(second_top_item["percentComplete"], percent_complete)

    def test_top_non_hvc_check_items_percent_is_descending(self):
        """ Check percentage value is in descending order """
        for i in range(6, 1, -1):
            for _ in range(0, i):
                self._create_non_hvc_win(export_value=100000, sector_id=self.TEAM_1_SECTORS[i], confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 5)
        self.assertTrue(response_decoded[0]["percentComplete"] >= response_decoded[1]["percentComplete"])
        self.assertTrue(response_decoded[1]["percentComplete"] >= response_decoded[2]["percentComplete"])
        self.assertTrue(response_decoded[2]["percentComplete"] >= response_decoded[3]["percentComplete"])
        self.assertTrue(response_decoded[3]["percentComplete"] >= response_decoded[4]["percentComplete"])

    def test_top_non_hvc_check_items_totalValue_is_descending(self):
        """ Check total value is in descending order """
        for i in range(6, 1, -1):
            for _ in range(0, i):
                self._create_non_hvc_win(export_value=100000, sector_id=self.TEAM_1_SECTORS[i], confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 5)
        self.assertTrue(response_decoded[0]["totalValue"] >= response_decoded[1]["totalValue"])
        self.assertTrue(response_decoded[1]["totalValue"] >= response_decoded[2]["totalValue"])
        self.assertTrue(response_decoded[2]["totalValue"] >= response_decoded[3]["totalValue"])
        self.assertTrue(response_decoded[3]["totalValue"] >= response_decoded[4]["totalValue"])

    def test_top_non_hvc_check_items_averageWinValue_is_descending(self):
        """ Check average Win Value is in descending order """
        for i in range(6, 1, -1):
            for _ in range(0, i):
                self._create_non_hvc_win(export_value=100000, sector_id=self.TEAM_1_SECTORS[i], confirm=True)

        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded), 5)
        self.assertTrue(response_decoded[0]["averageWinValue"] >= response_decoded[1]["averageWinValue"])
        self.assertTrue(response_decoded[1]["averageWinValue"] >= response_decoded[2]["averageWinValue"])
        self.assertTrue(response_decoded[2]["averageWinValue"] >= response_decoded[3]["averageWinValue"])
        self.assertTrue(response_decoded[3]["averageWinValue"] >= response_decoded[4]["averageWinValue"])


@freeze_time(SectorTeamBaseTestCase.frozen_date_17)
class SectorTeamWinTableTestCase(SectorTeamBaseTestCase, GenericWinTableTestMixin):
    win_date_2017 = datetime.datetime(2017, 5, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())
    st_win_table_url = reverse('mi:sector_team_win_table', kwargs={"team_id": 1})
    st_win_table_url_invalid = reverse('mi:sector_team_win_table', kwargs={"team_id": 100})
    export_value = 100000
    fin_years = [2017, 2016]
    TEST_COUNTRY_CODE = 'FR'
    TEST_CAMPAIGN_ID = 'E006'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.st_win_table_url
        self.expected_response = {
            "sector_team": {
                "id": "1",
                "name": "Financial & Professional Services",
            },
            "wins": {
                "hvc": []
            }
        }

    def test_2017_win_table_in_2016_404(self):
        self.view_base_url = self.st_win_table_url_invalid
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_win_table_in_2017_404(self):
        self.view_base_url = self.st_win_table_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

