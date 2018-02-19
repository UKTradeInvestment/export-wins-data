import json

from django.utils.datetime_safe import datetime
from django.utils.timezone import get_current_timezone

from sso.tests import BaseSSOTestCase


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
        assert hasattr(self, 'expected_response'), \
            'expected_response not added to TestCase class'
        self.assertJSONEqual(json.dumps(self._api_response_data), self.expected_response)

    def get_url_for_year(self, year, base_url):
        return '{base}?year={year}'.format(base=base_url, year=year)
