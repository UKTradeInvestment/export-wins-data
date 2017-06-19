import json

from django.contrib.auth.models import Group
from django.test import override_settings

from alice.tests.client import AliceClient
from sso.tests import BaseSSOTestCase
from users.factories import UserFactory
from wins.factories import HVCFactory


class MiApiViewsBaseTestCase(BaseSSOTestCase):
    maxDiff = None
    fin_start_date = "2016-04-01"
    frozen_date = "2016-11-01"
    fin_end_date = "2017-03-31"
    frozen_date_17 = "2017-05-01"

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
