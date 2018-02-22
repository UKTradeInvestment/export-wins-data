from uuid import UUID
from copy import deepcopy

from django.urls import reverse
from factory.fuzzy import FuzzyDate

from fdi.models import Investments, FinancialYear
from fdi.tests.base import FdiBaseTestCase
from fdi.factories import InvestmentFactory


FDIValueMapping = {
    UUID('38e36c77-61ad-4186-a7a8-ac6a1a1104c6'): 'high',
    UUID('002c18d9-f5c7-4f3c-b061-aee09fce8416'): 'good',
    UUID('2bacde8d-128f-4d0a-849b-645ceafe4cf9'): 'standard'
}

STAGES = ['won', 'prospect', 'active', 'assign_pm', 'verify_win']

class FDIOverviewTestCase(FdiBaseTestCase):
    maxDiff = None
    url = reverse('fdi:overview')
    factory = InvestmentFactory

    @property
    def empty_response(self):
        zero_count_and_percent = {
            "count": 0,
            "percent": 0.0
        }

        jobs = {
            "new": 0,
            "safeguarded": 0,
            "total": 0
        }

        stages = {k: deepcopy(zero_count_and_percent) for k in STAGES}
        campaign = {k: deepcopy(zero_count_and_percent) for k in ['hvc', 'non_hvc']}

        performance_section = {
            **zero_count_and_percent,
            'campaign': deepcopy(campaign),
            'jobs': deepcopy(jobs),
            'on_target': False
        }

        performance = {k: deepcopy(performance_section) for k in FDIValueMapping.values()}


        return deepcopy({
            "wins": {
                "count": 0,
                "total_investment_value__sum": 0,
                "jobs": deepcopy(jobs),
                "campaign": deepcopy(campaign),
                "performance": deepcopy(performance),
                "stages": deepcopy(stages)
            },
            "pipeline": {
                "active": {
                    "count": 0,
                    "total_investment_value__sum": 0,
                    "jobs": deepcopy(jobs),
                    "campaign": deepcopy(campaign),
                    "performance": deepcopy(performance),
                    "stages": deepcopy(stages)
                }
            },
            "stages": deepcopy(stages)
        })

    def assert_response_zeros(self, api_response):
        self.assertDictEqual(api_response, self.empty_response)

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
            self.url = self.get_url_for_year(year.id, base_url)
            for value_id in fdi_values:
                for stage in stages:
                    for hvc in hvcs:
                        msg = f'1 investment: value_id={value_id}, stage={stage}, year={year}, hvc={hvc}'
                        with self.subTest(value_id=value_id, stage=stage, year=year, hvc=hvc, msg=msg):
                            self._test_single_win(stage, value_id, year, hvc)
                        # clean up
                        Investments.objects.all().delete()

    def _test_single_win(self, stage, value_id, year, hvc):
        self.assertEqual(Investments.objects.count(), 0)
        hvc_code = 'I123' if hvc else None
        win = self.factory(
            fdi_value_id=value_id,
            stage=stage,
            hvc_code=hvc_code,
            date_won=FuzzyDate(year.start, min(year.end, self.frozen_date_17))
        )
        stage = stage.replace(' ', '_')

        self.assertEqual(Investments.objects.count(), 1)

        if stage == 'won':
            self.assertEqual(Investments.objects.won().count(), 1)

        self.assertEqual(Investments.objects.won_and_verify().count(), 1)

        # make api call
        api_response = self._api_response_data
        expected = self.empty_response

        wins = expected['wins']
        wins['count'] = 1
        wins['total_investment_value__sum'] = win.investment_value

        jobs = wins['jobs']
        jobs['new'] = win.number_new_jobs
        jobs['safeguarded'] = win.number_safeguarded_jobs
        jobs['total'] = win.number_safeguarded_jobs + win.number_new_jobs

        campaign = wins['campaign'] # type: dict
        hvc_path = 'hvc' if hvc else 'non_hvc'

        campaign[hvc_path]['count'] = 1
        campaign[hvc_path]['percent'] = 100.0

        value = FDIValueMapping[win.fdi_value_id]
        performance = wins['performance'][value] # type: dict
        performance['count'] = 1
        performance['percent'] = 100.0
        performance['campaign'][hvc_path]['count'] = 1
        performance['campaign'][hvc_path]['percent'] = 100.0
        performance['jobs']['new'] = win.number_new_jobs
        performance['jobs']['safeguarded'] = win.number_safeguarded_jobs
        performance['jobs']['total'] = win.number_safeguarded_jobs + win.number_new_jobs

        # TODO: handle 'on_target' later
        expected['wins']['performance']['high']['on_target'] = api_response['wins']['performance']['high']['on_target']
        expected['wins']['performance']['good']['on_target'] = api_response['wins']['performance']['good']['on_target']

        stage_part = wins['stages'][stage] # type: dict
        stage_part['count'] = 1
        stage_part['percent'] = 100.0

        global_stage_part = expected['stages'][stage] # type: dict
        global_stage_part['count'] = 1
        global_stage_part['percent'] = 100.0

        self.assertDictEqual(api_response, expected)
        Investments.objects.all().delete()

    def test_overview_no_wins_2016(self):
        self.url = self.get_url_for_year(2016, self.url)
        api_response = self._api_response_data
        self.assert_response_zeros(api_response)
