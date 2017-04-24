import datetime
import json
from operator import eq, gt

from django.core.urlresolvers import reverse
from factory.fuzzy import FuzzyDate
from freezegun import freeze_time

from mi.tests.test_sector_views import SectorTeamBaseTestCase


class SectorTeamNewFinancialYearTestCase(SectorTeamBaseTestCase):
    """ These tests are to check MI defaults to 2016-17 in the new FY 2017-18 """
    root_url_16 = reverse("mi:sector_teams") + "?year=2016"
    root_url_17 = reverse("mi:sector_teams") + "?year=2017"
    overview_url_16 = reverse("mi:sector_teams_overview") + "?year=2016"
    overview_url_17 = reverse("mi:sector_teams_overview") + "?year=2017"
    detail_url_16 = reverse("mi:sector_team_detail", kwargs={"team_id": 1}) + "?year=2016"
    detail_url_17 = reverse("mi:sector_team_detail", kwargs={"team_id": 1}) + "?year=2017"
    campaigns_url_16 = reverse("mi:sector_team_campaigns", kwargs={"team_id": 1}) + "?year=2016"
    campaigns_url_17 = reverse("mi:sector_team_campaigns", kwargs={"team_id": 1}) + "?year=2017"
    months_url_16 = reverse("mi:sector_team_months", kwargs={"team_id": 1}) + "?year=2016"
    months_url_17 = reverse("mi:sector_team_months", kwargs={"team_id": 1}) + "?year=2017"
    non_hvc_url_16 = reverse("mi:sector_team_top_non_hvc", kwargs={"team_id": 1}) + "?year=2016"
    non_hvc_url_17 = reverse("mi:sector_team_top_non_hvc", kwargs={"team_id": 1}) + "?year=2017"

    def _random_date_in_fy(self, fin_year=2016):
        """ generate a random date in the given financial year """
        return FuzzyDate(datetime.datetime(fin_year, 4, 1), datetime.datetime(fin_year + 1, 3, 31)).fuzz()

    def _add_test_data_for_fy(self, fin_year=2016, batch=25):
        """ Add few wins in given FY, ready for testing """
        for _ in range(batch):
            # add an unconfirmed hvc win
            random_date = self._random_date_in_fy(fin_year)
            self._create_hvc_win(win_date=random_date)

            # add a confirmed hvc win
            random_date = self._random_date_in_fy(fin_year)
            self._create_hvc_win(confirm=True,
                                 win_date=random_date,
                                 notify_date=random_date + datetime.timedelta(days=2),
                                 response_date=random_date + datetime.timedelta(days=3))

            # add an unconfirmed non-hvc win
            random_date = self._random_date_in_fy(fin_year)
            self._create_non_hvc_win(win_date=random_date)

            # add a confirmed non_hvc win
            random_date = self._random_date_in_fy(fin_year)
            self._create_non_hvc_win(confirm=True,
                                     win_date=random_date,
                                     notify_date=random_date + datetime.timedelta(days=2),
                                     response_date=random_date + datetime.timedelta(days=3))

    def _test_values_across_fy(self, url, check_func, *args):
        """
        function to test response is same irrespective of when we access
        Also checks any specific values that are passed in as check_func
        """
        with freeze_time("2017-03-31"):
            api_response = self._get_api_response(url)
            old_fy_response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            check_func(old_fy_response_decoded, *args)

        with freeze_time("2017-04-01"):
            api_response = self._get_api_response(url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(old_fy_response_decoded, response_decoded)
            check_func(response_decoded, *args)

        with freeze_time("2017-09-01"):
            api_response = self._get_api_response(url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(old_fy_response_decoded, response_decoded)
            check_func(response_decoded, *args)
            # self.assertEqual(response.status_code, 404)

    def test_sector_team_list(self):
        """ 
        Check sector team list across 2016 and 2017, only change should be 
        `Consumer & Creative` for 2016 and `Creative, Consumer and Sports` for 2017
        """
        api_response_16 = self._get_api_response(self.root_url_16)
        sector_team_list_16 = json.loads(api_response_16.content.decode("utf-8"))["results"]
        self.assertTrue(any(team["name"] == "Consumer & Creative" for team in sector_team_list_16))
        self.assertFalse(any(team["name"] == "Creative, Consumer and Sports" for team in sector_team_list_16))

    def test_sector_details(self):
        """ Check Sector details are loaded as expected in new FY """

        def check_values(response, relate):
            """ check few specific sector detail values """
            self.assertTrue(relate(response["wins"]["export"]["hvc"]["number"]["total"], 0))
            self.assertTrue(relate(response["wins"]["export"]["hvc"]["value"]["total"], 0))
            self.assertTrue(relate(response["wins"]["export"]["non_hvc"]["number"]["total"], 0))
            self.assertTrue(relate(response["wins"]["export"]["non_hvc"]["value"]["total"], 0))

        api_response = self._get_api_response(self.detail_url_16)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        check_values(response_decoded, eq)

        self._add_test_data_for_fy(fin_year=2015, batch=10)
        self._add_test_data_for_fy(fin_year=2016)
        self._add_test_data_for_fy(fin_year=2017, batch=10)
        self._test_values_across_fy(self.detail_url_16, check_values, gt)

    def test_sector_monthly(self):
        """ Check Sector team overview is loaded as expected in new FY """

        def check_values(response, relate):
            """ check if number of months returned """
            months = [month for month in response["months"]
                      if month["totals"]["export"]["hvc"]["value"]["total"] > 0]
            self.assertTrue(relate(len(months), 0))

        api_response = self._get_api_response(self.months_url_16)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        check_values(response_decoded, eq)

        self._add_test_data_for_fy(fin_year=2015, batch=10)
        self._add_test_data_for_fy(fin_year=2016)
        self._add_test_data_for_fy(fin_year=2017, batch=10)
        self._test_values_across_fy(self.months_url_16, check_values, gt)

    def test_sector_non_hvc_wins(self):
        """ Check Sector team top non-hvcs is loaded as expected in new FY """

        def check_values(response, relate):
            """ check number of non-hvc items in the response """
            self.assertTrue(relate(len(response), 0))

        api_response = self._get_api_response(self.non_hvc_url_16)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        check_values(response_decoded, eq)

        self._add_test_data_for_fy(fin_year=2015, batch=10)
        self._add_test_data_for_fy(fin_year=2016)
        self._add_test_data_for_fy(fin_year=2017, batch=10)
        self._test_values_across_fy(self.non_hvc_url_16, check_values, gt)

    def _test_team_data_across_fy(self, url, check_func, *args):
        """
        function to test team data is same across financial years
        Also checks any specific values that are passed in as check_func
        """
        with freeze_time("2017-03-31"):
            api_response = self._get_api_response(url)
            team_1_data_old = self._team_data(api_response.data["results"], 1)
            check_func(team_1_data_old, *args)

        with freeze_time("2017-04-01"):
            api_response = self._get_api_response(url)
            team_1_data_new = self._team_data(api_response.data["results"], 1)
            self.assertEqual(team_1_data_old, team_1_data_new)
            check_func(team_1_data_new, *args)

        with freeze_time("2017-09-01"):
            api_response = self._get_api_response(url)
            team_1_data_new = self._team_data(api_response.data["results"], 1)
            self.assertEqual(team_1_data_old, team_1_data_new)
            check_func(team_1_data_new, *args)

    def test_sector_overview(self):
        """ Check Sector team overview is loaded as expected in new FY """

        def check_values(response, relate):
            """ check hvc, non-hvc values returned in overview response """
            self.assertTrue(relate(response["values"]["hvc"]["current"]["confirmed"], 0))
            self.assertTrue(relate(response["values"]["hvc"]["current"]["unconfirmed"], 0))
            self.assertTrue(relate(response["values"]["hvc"]["target_percent"]["confirmed"], 0))
            self.assertTrue(relate(response["values"]["hvc"]["target_percent"]["unconfirmed"], 0))
            self.assertTrue(relate(response["values"]["hvc"]["total_win_percent"]["confirmed"], 0))
            self.assertTrue(relate(response["values"]["hvc"]["total_win_percent"]["unconfirmed"], 0))
            self.assertTrue(relate(response["values"]["non_hvc"]["current"]["confirmed"], 0))
            self.assertTrue(relate(response["values"]["non_hvc"]["current"]["unconfirmed"], 0))
            self.assertTrue(relate(response["values"]["non_hvc"]["total_win_percent"]["confirmed"], 0))
            self.assertTrue(relate(response["values"]["non_hvc"]["total_win_percent"]["unconfirmed"], 0))

        api_response = self._get_api_response(self.overview_url_16)
        team_1_data = self._team_data(api_response.data["results"], 1)
        check_values(team_1_data, eq)

        self._add_test_data_for_fy(fin_year=2015, batch=10)
        self._add_test_data_for_fy(fin_year=2016)
        self._add_test_data_for_fy(fin_year=2017, batch=10)
        self._test_team_data_across_fy(self.overview_url_16, check_values, gt)

    def _test_team_data_rag(self, check_func):
        """ extracting common functionality in overview rag tests """
        for hvc_code in self.TEAM_1_HVCS:
            for _ in range(5):
                # a win in 2016 FY
                random_date = self._random_date_in_fy(fin_year=2016)
                self._create_hvc_win(hvc_code=hvc_code, confirm=True, export_value=1000000,
                                     win_date=random_date,
                                     notify_date=random_date + datetime.timedelta(days=2),
                                     response_date=random_date + datetime.timedelta(days=3))
                # a win in 2017 FY
                random_date = self._random_date_in_fy(fin_year=2017)
                self._create_hvc_win(hvc_code=hvc_code, confirm=True, export_value=1000000,
                                     win_date=random_date,
                                     notify_date=random_date + datetime.timedelta(days=2),
                                     response_date=random_date + datetime.timedelta(days=3))

        self._test_team_data_across_fy(self.overview_url_16, check_func, gt)

    def test_sector_overview_rag(self):
        """
        Check Sector team overview, hvc_group rag status is loaded as expected in new FY
        As there are no wins yet, all HVC's are tagged as red
        With enough wins, we should push some of them into green, still within old FY
        When we check the same after crossing into new FY, should still be the same
        """

        def check_values(response, relate):
            """ check green status performance """
            self.assertTrue(relate(response["hvc_performance"]["green"], 0))

        api_response = self._get_api_response(self.overview_url_16)
        team_1_data = self._team_data(api_response.data["results"], 1)

        self.assertTrue(team_1_data["hvc_performance"]["green"] == 0)
        self.assertTrue(team_1_data["hvc_performance"]["amber"] == 0)
        self.assertTrue(team_1_data["hvc_performance"]["red"] > 0)

        self._test_team_data_rag(check_values)

    def test_sector_overview_hvc_groups_rag(self):
        """
        Check HVC groups within Sector team overview rag status is loaded as expected in new FY
        As there are no wins yet, all HVC's are tagged as red
        With enough wins, we should push some of them into green, still within old FY
        When we check the same after crossing into new FY, should still be the same
        """

        def check_values(response, relate):
            """ check green hvc_group's status performance """
            for hvc_group in response["hvc_groups"]:
                self.assertTrue(
                    relate(hvc_group["hvc_performance"]["green"], 0) or
                    relate(hvc_group["hvc_performance"]["amber"], 0)
                )
            self.assertTrue(relate(response["hvc_groups"][0]["hvc_performance"]["green"], 0))

        api_response = self._get_api_response(self.overview_url_16)
        team_1_data = self._team_data(api_response.data["results"], 1)

        self.assertTrue(team_1_data["hvc_groups"][0]["hvc_performance"]["green"] == 0)
        self.assertTrue(team_1_data["hvc_groups"][0]["hvc_performance"]["amber"] == 0)
        self.assertTrue(team_1_data["hvc_groups"][0]["hvc_performance"]["red"] > 0)

        self._test_team_data_rag(check_values)
