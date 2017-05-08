import json

from django.contrib.auth.models import Group
from django.test import override_settings, TestCase

from alice.tests.client import AliceClient
from users.factories import UserFactory
from wins.factories import HVCFactory


class MiApiViewsBaseTestCase(TestCase):
    maxDiff = None
    fin_start_date = "2016-04-01"
    frozen_date = "2016-11-01"
    fin_end_date = "2017-03-31"

    TEAM_1_HVCS = ['E006', 'E019', 'E031', 'E072', 'E095', 'E115', 'E128', 'E160', 'E167', 'E191']
    TEAM_1_SECTORS = [60, 61, 62, 63, 64, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159,
                      160, 161, 162, 163, 164, 165, 166, 167, 168, 169]
    SAMPLE_COUNTRIES = ['CA', 'BS', 'GQ', 'VA', 'AQ', 'SA', 'EG', 'LU', 'ER', 'GA', 'MP']
    CAMPAIGN_TARGET = 10000000

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice_client = AliceClient()

        cls.user = UserFactory.create()
        cls.user.set_password("asdf")
        cls.user.save()

        mi_group = Group.objects.get(name="mi_group")
        mi_group.user_set.add(cls.user)

        # needed to get names of HVCs, have to do again because factory
        # remembers other tests, even if flushed from DB
        for i in range(255):
            HVCFactory.create(
                campaign_id='E%03d' % (i + 1),
                financial_year=16,
            )

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def _get_api_response(self, url, status_code=200):
        self.alice_client.login(username=self.user.email, password="asdf")
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, status_code)
        return response

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
        api_response_result = json.loads(self._api_response_json)["results"]
        self.assertJSONEqual(json.dumps(api_response_result), self.expected_response)
