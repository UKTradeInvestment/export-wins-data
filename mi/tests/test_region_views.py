from django.urls import reverse
from unittest import mock

from mi.models import OverseasRegionGroup, OverseasRegion, FinancialYear, OverseasRegionGroupYear
from mi.tests.base_test_case import MiApiViewsBaseTestCase
from mi.views.region_views import BaseOverseasRegionGroupMIView


class BaseOverseasRegionGroupMIViewTestCase(MiApiViewsBaseTestCase):
    view_class = BaseOverseasRegionGroupMIView

    def setUp(self):
        super().setUp()
        self.view = self.view_class()
        self.all_os_region_groups = list(OverseasRegionGroup.objects.all())

    def test_queryset_is_unfiltered(self):
        self.assertEqual(
            len(self.all_os_region_groups),
            self.view.get_queryset().count()
        )

    def test_get_result_uses_serializer(self):
        with mock.patch('mi.views.region_views.OverseasRegionGroupSerializer') as mocked_serializer:
            mocked_serializer.data = {}
            self.view.get_results()
            self.assertTrue(mocked_serializer.called)
            self.assertEqual(
                len(mocked_serializer.call_args_list),
                len(self.all_os_region_groups)
            )


class OverseasRegionGroupListViewTestCase(MiApiViewsBaseTestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @classmethod
    def setUpTestData(cls):
        # clear out existing hierarchy for this test
        OverseasRegion.objects.all().delete()
        OverseasRegionGroup.objects.all().delete()
        OverseasRegionGroupYear.objects.all().delete()

        cls.fy2017 = FinancialYear.objects.get(id=2017)
        cls.fy2016 = FinancialYear.objects.get(id=2016)
        cls.region1 = OverseasRegion.objects.create(name='test1')
        cls.region2 = OverseasRegion.objects.create(name='test2')
        cls.group1 = OverseasRegionGroup.objects.create(name='group 1')
        cls.group2 = OverseasRegionGroup.objects.create(name='group 2')

        OverseasRegionGroupYear.objects.create(
            group=cls.group1, financial_year=cls.fy2016, region=cls.region1)
        OverseasRegionGroupYear.objects.create(
            group=cls.group2, financial_year=cls.fy2017, region=cls.region2)

    def test_os_region_groups_list_2016(self):
        """ test `OverseasRegionGroup` list API"""
        self.url = reverse('mi:overseas_region_groups') + "?year=2016"
        self.expected_response = [
            {
                'name': 'group 1',
                'id': self.group1.id,
                'regions': [{'name': 'test1', 'id': self.region1.id}]
            }
        ]

    def test_os_region_groups_list_2017(self):
        """ test `OverseasRegionGroup` list API"""
        self.url = reverse('mi:overseas_region_groups') + "?year=2017"
        self.expected_response = [
            {
                'name': 'group 2',
                'id': self.group2.id,
                'regions': [{'name': 'test2', 'id': self.region2.id}]
            }
        ]

        self.assertResponse()

    def test_os_region_groups_list_no_duplicates(self):
        """ test `OverseasRegionGroup` list API"""
        OverseasRegionGroupYear.objects.create(
            group=self.group1, financial_year=self.fy2017, region=self.region1)
        self.url = reverse('mi:overseas_region_groups') + "?year=2017"
        self.expected_response = [
            {
                'name': 'group 1',
                'id': self.group1.id,
                'regions': [{'name': 'test1', 'id': self.region1.id}]
            },
            {
                'name': 'group 2',
                'id': self.group2.id,
                'regions': [{'name': 'test2', 'id': self.region2.id}]
            }
        ]

        self.assertResponse()

class OverseasRegionListViewTestCase(MiApiViewsBaseTestCase):

    def test_list_returns_only_countries_for_2016(self):
        self.url = reverse('mi:overseas_regions') + '?year=2016'
        response_data = self._api_response_data
        self.assertEqual(
            17,
            len(response_data)
        )
        countries = {x['name'].lower() for x in response_data}

        # Africa region should only be in 2017 data
        self.assertFalse('africa' in countries)

        self.assertTrue('north africa' in countries)

    def test_list_only_returns_countries_for_2017(self):
        self.url = reverse('mi:overseas_regions') + '?year=2017'
        response_data = self._api_response_data
        self.assertEqual(
            15,
            len(response_data)
        )

        countries = {x['name'].lower() for x in response_data}
        self.assertTrue('africa' in countries)

        # North Africa removed in 2017
        self.assertTrue('north africa' in countries)
