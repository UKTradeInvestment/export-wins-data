from django.urls import reverse
from toolz import get_in

from fdi.tests.base import FdiBaseTestCase

class FDIOverviewTestCase(FdiBaseTestCase):
    url = reverse('fdi:overview')

    def assert_response_zeros(self, api_response):
        wins_base_path = ['wins']
        pipeline_base_path = ['pipeline']
        pipeline_active_path = pipeline_base_path + ['active']
        paths = [
            wins_base_path + ['count'],
            wins_base_path + ['total_investment_value__sum'],
            wins_base_path + ['jobs', 'new'],
            wins_base_path + ['jobs', 'safeguarded'],
            wins_base_path + ['jobs', 'total'],
            wins_base_path + ['campaign', 'hvc', 'count'],
            wins_base_path + ['campaign', 'hvc', 'percent'],
            wins_base_path + ['campaign', 'non_hvc', 'count'],
            wins_base_path + ['campaign', 'non_hvc', 'percent'],
        ]
        for v in ['high', 'good', 'standard']:
            for base in [wins_base_path, pipeline_active_path]:
                performance_base_path = base + ['performance']

                performance_paths = [
                    performance_base_path + [v, 'count'],
                    performance_base_path + [v, 'percent'],
                    performance_base_path + [v, 'campaign', 'hvc', 'count'],
                    performance_base_path + [v, 'campaign', 'hvc', 'percent'],
                    performance_base_path + [v, 'campaign', 'non_hvc', 'count'],
                    performance_base_path + [v, 'campaign', 'non_hvc', 'percent'],
                    performance_base_path + [v, 'jobs', 'new'],
                    performance_base_path + [v, 'jobs', 'safeguarded'],
                    performance_base_path + [v, 'jobs', 'total'],
                    performance_base_path + [v, 'on_target'],
                ]
                paths.extend(performance_paths)
        for stage in ['won', 'prospect', 'active', 'assign_pm', 'verify_win']:
            for base in [wins_base_path, pipeline_active_path, []]:
                stage_paths = [
                    base + ['stages', stage, 'count'],
                    base + ['stages', stage, 'percent']
                ]
                paths.extend(stage_paths)
        for path in paths:
            self.assertEqual(get_in(path, api_response, no_default=True), 0, path)

    def test_overview_no_wins_2017(self):
        self.url = self.get_url_for_year(2017, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)


    def test_overview_no_wins_2016(self):
        self.url = self.get_url_for_year(2016, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)
