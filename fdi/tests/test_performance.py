from datetime import timedelta
from itertools import product, permutations
from typing import List, Tuple, Dict, NewType, Union
from uuid import UUID

from django.urls import reverse
from django.utils.functional import cached_property
from toolz import get_in, iterate, identity

from fdi.models import Investments, FinancialYear
from fdi.tests.base import FdiBaseTestCase
from fdi.factories import InvestmentFactory
from fdi.tests.util import PathDict

PathsAndExpected = NewType('PathsAndExpected', Dict[Union[Tuple[str, ...], str], int])

FDIValueMapping = {
    UUID('38e36c77-61ad-4186-a7a8-ac6a1a1104c6'): 'high',
    UUID('002c18d9-f5c7-4f3c-b061-aee09fce8416'): 'good',
    UUID('2bacde8d-128f-4d0a-849b-645ceafe4cf9'): 'standard'
}

class FDIOverviewTestCase(FdiBaseTestCase):
    url = reverse('fdi:overview')
    factory = InvestmentFactory

    @cached_property
    def all_paths(self) -> List[Tuple[str, ...]]:
        wins_base_path = ('wins',)
        pipeline_base_path = ('pipeline',)
        pipeline_active_path = pipeline_base_path + ('active',)
        paths = [
            wins_base_path + ('count',),
            wins_base_path + ('total_investment_value__sum',),
            wins_base_path + ('jobs', 'new',),
            wins_base_path + ('jobs', 'safeguarded',),
            wins_base_path + ('jobs', 'total',),
            wins_base_path + ('campaign', 'hvc', 'count',),
            wins_base_path + ('campaign', 'hvc', 'percent',),
            wins_base_path + ('campaign', 'non_hvc', 'count',),
            wins_base_path + ('campaign', 'non_hvc', 'percent',),
            ]
        for v in ['high', 'good', 'standard']:
            for base in [wins_base_path, pipeline_active_path]:
                performance_base_path = base + ('performance',)

                performance_paths = [
                    performance_base_path + (v, 'count',),
                    performance_base_path + (v, 'percent',),
                    performance_base_path + (v, 'campaign', 'hvc', 'count',),
                    performance_base_path + (v, 'campaign', 'hvc', 'percent',),
                    performance_base_path + (v, 'campaign', 'non_hvc', 'count',),
                    performance_base_path + (v, 'campaign', 'non_hvc', 'percent',),
                    performance_base_path + (v, 'jobs', 'new',),
                    performance_base_path + (v, 'jobs', 'safeguarded',),
                    performance_base_path + (v, 'jobs', 'total',),
                    performance_base_path + (v, 'on_target',),
                    ]
                paths.extend(performance_paths)
        for stage in ['won', 'prospect', 'active', 'assign_pm', 'verify_win']:
            for base in [wins_base_path, pipeline_active_path, ()]:
                stage_paths = [
                    base + ('stages', stage, 'count',),
                    base + ('stages', stage, 'percent',)
                ]
                paths.extend(stage_paths)
        return paths

    @property
    def all_paths_with_zero_expected(self) -> PathsAndExpected:
        zeros = iterate(identity, 0)
        return PathDict(zip(self.all_paths, zeros))

    def assert_path_and_expected(self, api_response, paths_and_expected: PathsAndExpected):
        for path, expected in paths_and_expected.items():
            dotted_path = '.'.join(list(path))
            actual = get_in(path, api_response)
            self.assertEqual(
                actual,
                expected,
                f'{dotted_path} was: {actual}, expected: {expected}'
            )

    def assert_response_zeros(self, api_response):
        self.assert_path_and_expected(api_response, self.all_paths_with_zero_expected)

    def test_overview_no_wins_2017(self):
        self.url = self.get_url_for_year(2017, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)

    def test_overview_1_win_all_fdi_values_won_and_verify_win(self):
        fdi_values = FDIValueMapping.keys()
        stages = ['won', 'verify win']
        hvcs = [True, False]
        years = FinancialYear.objects.all()
        base_url = self.url
        for year in years:
            self.url = self.get_url_for_year(2017, base_url)
            for value_id in fdi_values:
                for stage in stages:
                    for hvc in hvcs:
                        with self.subTest(value_id=value_id, stage=stage, year=year):
                            self._test_single_win(stage, value_id, hvc=hvc)

    def _test_single_win(self, stage, value_id, hvc):
        self.assertEqual(Investments.objects.count(), 0)
        hvc_code = 'I123' if hvc else None
        win = self.factory(fdi_value_id=value_id, stage=stage, hvc_code=hvc_code)
        stage = stage.replace(' ', '_')
        self.assertEqual(Investments.objects.count(), 1)
        if stage == 'won':
            self.assertEqual(Investments.objects.won().count(), 1)
        self.assertEqual(Investments.objects.won_and_verify().count(), 1)
        api_response = self._api_response_data
        expected = self.all_paths_with_zero_expected
        expected['wins.count'] = 1
        expected['wins.total_investment_value__sum'] = win.investment_value
        expected['wins.jobs.new'] = win.number_new_jobs
        expected['wins.jobs.safeguarded'] = win.number_safeguarded_jobs
        expected['wins.jobs.total'] = win.number_safeguarded_jobs + win.number_new_jobs

        hvc_path = 'hvc' if hvc else 'non_hvc'
        expected[f'wins.campaign.{hvc_path}.count'] = 1
        expected[f'wins.campaign.{hvc_path}.percent'] = 100

        expected[('wins', 'performance', FDIValueMapping[win.fdi_value_id], 'count')] = 1
        expected[('wins', 'performance', FDIValueMapping[win.fdi_value_id], 'percent')] = 100
        expected[('wins', 'performance', FDIValueMapping[win.fdi_value_id], 'campaign', hvc_path, 'count')] = 1
        expected[('wins', 'performance', FDIValueMapping[win.fdi_value_id], 'campaign', hvc_path, 'percent')] = 100
        expected[('wins', 'performance', FDIValueMapping[win.fdi_value_id], 'jobs', 'new')] = win.number_new_jobs
        expected[(
        'wins', 'performance', FDIValueMapping[win.fdi_value_id], 'jobs', 'safeguarded')] = win.number_safeguarded_jobs
        expected[('wins', 'performance', FDIValueMapping[win.fdi_value_id], 'jobs',
                  'total')] = win.number_safeguarded_jobs + win.number_new_jobs
        del expected['wins.performance.high.on_target']
        del expected['wins.performance.good.on_target']
        expected[('wins', 'stages', stage, 'count')] = 1
        expected[('wins', 'stages', stage, 'percent')] = 100
        expected[('stages', stage, 'count')] = 1
        expected[('stages', stage, 'percent')] = 100
        self.assert_path_and_expected(api_response, expected)
        Investments.objects.all().delete()

    def test_overview_no_wins_2016(self):
        self.url = self.get_url_for_year(2016, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)
