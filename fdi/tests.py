from django.test import TestCase
from django.urls import reverse
from django.utils.datetime_safe import datetime
from django.utils.timezone import get_current_timezone

from freezegun import freeze_time
import json

from sso.tests import BaseSSOTestCase
from fdi.factories import InvestmentFactory


class FdiBaseTestCase(BaseSSOTestCase):
    fixtures = [
        'fdivalues_data.json', 'investmenttype_data.json', 'involvement_data.json',
        'sector_data.json', 'specificprogramme_data.json', 'uk_region_data.json'
    ]

    frozen_date_17 = datetime(2017, 5, 28, tzinfo=get_current_timezone())

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

    def get_url_for_year(self, year, base_url):
        return '{base}?year={year}'.format(base=base_url, year=year)


@freeze_time(FdiBaseTestCase.frozen_date_17)
class SectorTeamListTestCase(FdiBaseTestCase):
    """
    Tests covering SectorTeam overview and detail API endpoints
    """

    url = reverse("fdi:sector_teams") + "?year=2017"

    def test_sector_teams_list(self):
        """ test `SectorTeam` list API """

        self.expected_response = sorted([
            {
                "id": 1,
                "name": "Aero",
                "description": "Aerospace"
            },
            {
                "id": 2,
                "name": "AESC",
                "description": "Advanced Engineering and Supply Chains"
            },
            {
                "id": 3,
                "name": "Agri",
                "description": "Agriculture"
            },
            {
                "id": 4,
                "name": "Auto",
                "description": "Automotive"
            },
            {
                "id": 5,
                "name": "BPS",
                "description": "Business and Professional Services"
            },
            {
                "id": 6,
                "name": "Chem",
                "description": "Chemicals"
            },
            {
                "id": 7,
                "name": "Creative",
                "description": "Creative"
            },
            {
                "id": 8,
                "name": "D&S",
                "description": "Defence and Security"
            },
            {
                "id": 9,
                "name": "F&D",
                "description": "Food and Drink"
            },
            {
                "id": 10,
                "name": "FS",
                "description": "Financial Services"
            },
            {
                "id": 11,
                "name": "Infrastructure",
                "description": "Infrastructure"
            },
            {
                "id": 12,
                "name": "Life S",
                "description": "Life Sciences"
            },
            {
                "id": 13,
                "name": "Marine",
                "description": "Marine"
            },
            {
                "id": 14,
                "name": "Nuclear",
                "description": "Nuclear Energy"
            },
            {
                "id": 15,
                "name": "O&G",
                "description": "Oil and Gas"
            },
            {
                "id": 16,
                "name": "Rail",
                "description": "Railways"
            },
            {
                "id": 17,
                "name": "Renew",
                "description": "Renewable Energy"
            },
            {
                "id": 18,
                "name": "Retail",
                "description": "Retail"
            },
            {
                "id": 19,
                "name": "Space",
                "description": "Space"
            },
            {
                "id": 20,
                "name": "Tech",
                "description": "Technology"
            },
            {
                "id": 21,
                "name": "Other",
                "description": "Other"
            }
        ], key=lambda x: (x["id"]))
        self.assertResponse()


class FDIOverviewTestCase(FdiBaseTestCase):
    url = reverse('fdi:overview')

    def test_overview_no_wins_2017(self):
        self.url = self.get_url_for_year(2017, self.url)
        api_response = self._api_response_data
        self.assertEqual(api_response["performance"]["verified"]["good"]["count"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["investment_value__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["value__percent"], 0)

        self.assertEqual(api_response["performance"]["verified"]["high"]["count"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["investment_value__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["value__percent"], 0)

        self.assertEqual(api_response["performance"]["verified"]["standard"]["count"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["investment_value__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["value__percent"], 0)

        self.assertEqual(api_response["total"]["verified"]["count"], 0)
        self.assertEqual(api_response["total"]["verified"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["verified"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["verified"]["investment_value__sum"], 0)

        self.assertEqual(api_response["total"]["pending"]["count"], 0)
        self.assertEqual(api_response["total"]["pending"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["pending"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["pending"]["investment_value__sum"], 0)

        self.assertEqual(api_response["verified_met_percent"], 0)

    def test_overview_no_wins_2016(self):
        self.url = self.get_url_for_year(2016, self.url)
        api_response = self._api_response_data
        self.assertEqual(api_response["performance"]["verified"]["good"]["count"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["investment_value__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["good"]["value__percent"], 0)

        self.assertEqual(api_response["performance"]["verified"]["high"]["count"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["investment_value__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["high"]["value__percent"], 0)

        self.assertEqual(api_response["performance"]["verified"]["standard"]["count"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["investment_value__sum"], 0)
        self.assertEqual(api_response["performance"]["verified"]["standard"]["value__percent"], 0)

        self.assertEqual(api_response["total"]["verified"]["count"], 0)
        self.assertEqual(api_response["total"]["verified"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["verified"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["verified"]["investment_value__sum"], 0)

        self.assertEqual(api_response["total"]["pending"]["count"], 0)
        self.assertEqual(api_response["total"]["pending"]["number_new_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["pending"]["number_safeguarded_jobs__sum"], 0)
        self.assertEqual(api_response["total"]["pending"]["investment_value__sum"], 0)

        self.assertEqual(api_response["verified_met_percent"], 0)
