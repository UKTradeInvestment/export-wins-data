import json
from uuid import UUID

from django.utils.datetime_safe import datetime
from django.utils.timezone import get_current_timezone

from sso.tests import BaseSSOTestCase

FDIValueMapping = {
    UUID('38e36c77-61ad-4186-a7a8-ac6a1a1104c6'): 'high',
    UUID('002c18d9-f5c7-4f3c-b061-aee09fce8416'): 'good',
    UUID('2bacde8d-128f-4d0a-849b-645ceafe4cf9'): 'standard'
}

STAGES = ['won', 'prospect', 'active', 'assign_pm', 'verify_win']


class FdiBaseTestCase(BaseSSOTestCase):
    fixtures = [
        'fdivalues_data.json', 'investmenttype_data.json', 'involvement_data.json',
        'sector_data.json', 'specificprogramme_data.json', 'uk_region_data.json',
        'markets.json', 'markets_country.json', 'overseas_region.json',
        'overseas_region_market.json', 'markets_group.json', 'markets_group_country.json',
        'markets_target.json', 'sector_team_target.json'
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
        assert hasattr(self, 'expected_response'), \
            'expected_response not added to TestCase class'
        self.assertJSONEqual(json.dumps(
            self._api_response_data), self.expected_response)

    def get_url_for_year(self, year, base_url):
        return '{base}?year={year}'.format(base=base_url, year=year)
