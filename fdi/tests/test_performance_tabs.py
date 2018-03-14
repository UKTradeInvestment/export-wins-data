from django.urls import reverse
from toolz import get_in

from fdi.tests.base import FdiBaseTestCase


class FDIOverviewTabsTestCase(FdiBaseTestCase):
    url = reverse('fdi:tab_overview', kwargs={'name': 'sector'})

    def assert_response_zeros(self, api_response):
        for team in api_response:
            self.assertEqual(team['wins']['verify_win']['count'], 0)
            self.assertEqual(team['wins']['verify_win']['percent'], 0.0)
            self.assertEqual(team['wins']['won']['count'], 0)
            self.assertEqual(team['wins']['won']['percent'], 0)
            self.assertEqual(team['wins']['hvc']['count'], 0)
            self.assertEqual(team['wins']['hvc']['percent'], 0)
            self.assertEqual(team['wins']['non_hvc']['count'], 0)
            self.assertEqual(team['wins']['non_hvc']['percent'], 0)
            self.assertEqual(team['wins']['total'], 0)
            self.assertEqual(team['pipeline'], 0)
            self.assertEqual(team['total_jobs'], 0)
            self.assertTrue(team['target'] >= 0)

    def test_overview_sector_tab_no_wins_2017(self):
        self.url = reverse('fdi:tab_overview', kwargs={'name': 'sector'})
        self.url = self.get_url_for_year(2017, self.url)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 21)
        self.assert_response_zeros(api_response)

    def test_overview_sector_tab_no_wins_2016(self):
        self.url = reverse('fdi:tab_overview', kwargs={'name': 'sector'})
        self.url = self.get_url_for_year(2016, self.url)
        api_response = self._api_response_data
        self.assertEqual(len(api_response), 21)
        self.assert_response_zeros(api_response)

    def test_overview_region_tab_no_wins_2017(self):
        self.url = reverse('fdi:tab_overview', kwargs={'name': 'os_region'})
        self.url = self.get_url_for_year(2017, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)

    def test_overview_region_tab_no_wins_2016(self):
        self.url = reverse('fdi:tab_overview', kwargs={'name': 'os_region'})
        self.url = self.get_url_for_year(2016, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)
