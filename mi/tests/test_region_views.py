import datetime
import json

from django.utils.timezone import now, get_current_timezone
from unittest import mock

from freezegun import freeze_time
from jmespath import search as s

from django.urls import reverse
from django.core.management import call_command

from fixturedb.factories.win import create_win_factory
from mi.models import OverseasRegionGroup, OverseasRegion, FinancialYear, OverseasRegionGroupYear, OverseasRegionYear
from mi.tests.base_test_case import MiApiViewsBaseTestCase, MiApiViewsWithWinsBaseTestCase
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


class OverseasRegionBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):

    view_base_url = reverse('mi:overseas_regions')

    def get_url_for_year(self, year):
        return '{base}?year={year}'.format(base=self.view_base_url, year=year)

    def assert_result_count(self, expected_length):
        self.assertEqual(
            expected_length,
            len(self._api_response_data)
        )

    @property
    def countries(self):
        return {x['name'].lower() for x in self._api_response_data}


class OverseasRegionListViewTestCase(OverseasRegionBaseViewTestCase):
    view_base_url = reverse('mi:overseas_region_overview')

    def test_list_returns_only_countries_for_2016(self):
        self.url = self.get_url_for_year(2016)
        self.assert_result_count(17)

        # Africa region should only be in 2017 data
        self.assertFalse('africa' in self.countries)
        self.assertTrue('north africa' in self.countries)

    def test_list_only_returns_countries_for_2017(self):
        self.url = self.get_url_for_year(2017)
        self.assert_result_count(15)
        self.assertTrue('africa' in self.countries)
        # North Africa still in 2017
        self.assertTrue('north africa' in self.countries)


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class OverseasRegionOverviewTestCase(OverseasRegionBaseViewTestCase):
    view_base_url = reverse('mi:overseas_region_overview')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.export_value = 777777

    def test_list_returns_only_countries_for_2016(self):
        self.url = self.get_url_for_year(2016)
        self.assert_result_count(17)

        # Africa region should only be in 2017 data
        self.assertFalse('africa' in self.countries)
        self.assertTrue('north africa' in self.countries)

    def test_list_only_returns_countries_for_2017(self):
        self.url = self.get_url_for_year(2017)
        self.assert_result_count(15)
        self.assertTrue('africa' in self.countries)
        # North Africa still in 2017
        self.assertTrue('north africa' in self.countries)

    def test_overview_value_1_win(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=True, fin_year=2017, export_value=self.export_value)
        self.assertEqual(w1.country.code, 'CA')
        self.url = self.get_url_for_year(2017)
        data = self._api_response_data
        na_data = [x for x in data if x['name'] == 'North America'][0]
        self.assertEqual(w1.total_expected_export_value, na_data[
                         'values']['hvc']['current']['confirmed'])

    def test_overview_value_2_wins_same_region(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=True, fin_year=2017, export_value=self.export_value)
        w2 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=True, fin_year=2017, export_value=1)
        self.assertEqual(w1.country.code, w2.country.code)
        self.url = self.get_url_for_year(2017)
        data = self._api_response_data
        na_data = [x for x in data if x['name'] == 'North America'][0]
        self.assertEqual(w1.total_expected_export_value + 1,
                         na_data['values']['hvc']['current']['confirmed'])

    def test_overview_value_2_wins_different_regions(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=True, fin_year=2017, export_value=self.export_value)
        w2 = self._create_hvc_win(hvc_code='E119', win_date=now(
        ), confirm=True, fin_year=2017, export_value=1)
        self.assertEqual(w1.country.code, w2.country.code)
        self.url = self.get_url_for_year(2017)
        data = self._api_response_data
        na_data = [x for x in data if x['name'] == 'North America'][0]
        we_data = [x for x in data if x['name'] == 'Western Europe'][0]
        self.assertEqual(w1.total_expected_export_value, na_data[
                         'values']['hvc']['current']['confirmed'])
        self.assertEqual(w2.total_expected_export_value, we_data[
                         'values']['hvc']['current']['confirmed'])

    def test_overview_1_unconfirmed_and_1_confirmed_same_year(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=True, fin_year=2017, export_value=self.export_value)
        w2 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=False, fin_year=2017, export_value=1)
        self.assertEqual(w1.country.code, w2.country.code)
        self.url = self.get_url_for_year(2017)
        data = self._api_response_data
        na_data = [x for x in data if x['name'] == 'North America'][0]
        self.assertEqual(w1.total_expected_export_value, na_data[
                         'values']['hvc']['current']['confirmed'])
        self.assertEqual(w2.total_expected_export_value, na_data[
                         'values']['hvc']['current']['unconfirmed'])

    def test_overview_1_unconfirmed_in_current_year_should_not_show_up_in_last_year(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=now(
        ), confirm=False, fin_year=2017, export_value=self.export_value)
        self.url = self.get_url_for_year(2017)
        data = self._api_response_data
        na_data = [x for x in data if x['name'] == 'North America'][0]
        self.assertEqual(w1.total_expected_export_value, na_data[
                         'values']['hvc']['current']['unconfirmed'])
        self.assertEqual(0, na_data['values']['hvc']['current']['confirmed'])

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        self.assertEqual(
            0,
            s("sum([?name=='North America'].values.*.current[].[confirmed,unconfirmed][])", data_2016)
        )

    def test_overview_1_unconfirmed_last_year_should_not_show_up_in_last_year(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=self.frozen_date,
                                  confirm=False, fin_year=2016, export_value=self.export_value)

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        self.assertEqual(
            0,
            s("sum([?name=='North America'].values.*.current[].[confirmed,unconfirmed][])", data_2016)
        )

        # it should be in this year
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = [x for x in data_2017 if x[
            'name'] == 'North America'][0]
        self.assertEqual(w1.total_expected_export_value, na_data_2017[
                         'values']['hvc']['current']['unconfirmed'])

    def test_overview_1_unconfirmed_last_year_should_show_up_in_new_region_if_country_has_moved_regions(self):
        w1 = self._create_hvc_win(hvc_code='E016', win_date=self.frozen_date,
                                  confirm=False, fin_year=2016, export_value=self.export_value)

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        na_data_2016 = [x for x in data_2016 if x[
            'name'] == 'North America'][0]
        self.assertEqual(0, na_data_2016['values'][
                         'hvc']['current']['confirmed'])
        self.assertEqual(0, na_data_2016['values'][
                         'hvc']['current']['unconfirmed'])
        self.assertEqual(w1.country.code, 'CA')

        # move Canada to a different region
        region_year = OverseasRegionYear.objects.get(
            country__country='CA', financial_year_id=2017)
        region_year.overseas_region = OverseasRegion.objects.get(
            name='Western Europe')
        region_year.save()

        # it should be in this year
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = s("[?name=='North America']|[0]", data_2017)
        we_data_2017 = s("[?name=='Western Europe']|[0]", data_2017)

        self.assertEqual(0, na_data_2017['values'][
                         'hvc']['current']['unconfirmed'])
        self.assertEqual(w1.total_expected_export_value, we_data_2017[
                         'values']['hvc']['current']['unconfirmed'])

    # Non HVC
    def test_non_hvc_win_in_overview_confirmed_current_year(self):
        w1 = self._create_non_hvc_win(
            win_date=self.frozen_date_17, export_value=self.export_value, confirm=True, country='CA', fin_year=2017)
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = s("[?name=='North America']|[0]", data_2017)
        self.assertEqual(w1.total_expected_export_value, na_data_2017[
                         'values']['non_hvc']['current']['confirmed'])

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        self.assertEqual(
            0,
            s("sum([?name=='North America'].values.*.current[].[confirmed,unconfirmed][])", data_2016)
        )

    def test_non_hvc_win_in_overview_unconfirmed_current_year(self):
        w1 = self._create_non_hvc_win(
            win_date=self.frozen_date_17, export_value=self.export_value, confirm=False, country='CA', fin_year=2017)
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = s("[?name=='North America']|[0]", data_2017)
        self.assertEqual(w1.total_expected_export_value, na_data_2017[
                         'values']['non_hvc']['current']['unconfirmed'])

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        self.assertEqual(
            0,
            s("sum([?name=='North America'].values.*.current[].[confirmed,unconfirmed][])", data_2016)
        )

    def test_2_non_hvc_win_in_overview_both_confirmed_current_year(self):
        self._create_non_hvc_win(win_date=self.frozen_date_17,
                                 export_value=self.export_value + 1, confirm=True, country='CA', fin_year=2017)
        self._create_non_hvc_win(win_date=self.frozen_date_17,
                                 export_value=self.export_value - 1, confirm=True, country='CA', fin_year=2017)
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = s("[?name=='North America']|[0]", data_2017)

        self.assertEqual(self.export_value * 2,
                         na_data_2017['values']['non_hvc']['current']['confirmed'])

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        self.assertEqual(
            0,
            s("sum([?name=='North America'].values.*.current[].[confirmed,unconfirmed][])", data_2016)
        )

    def test_2_non_hvc_win_in_overview_confirmed_and_unconfirmed_current_year(self):
        w1 = self._create_non_hvc_win(
            win_date=self.frozen_date_17,
            export_value=self.export_value + 1,
            confirm=True,
            country='CA',
            fin_year=2017
        )
        w2 = self._create_non_hvc_win(
            win_date=self.frozen_date_17,
            export_value=self.export_value - 1,
            confirm=False,
            country='CA',
            fin_year=2017
        )
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = s("[?name=='North America']|[0]", data_2017)
        self.assertEqual(w1.total_expected_export_value, na_data_2017[
                         'values']['non_hvc']['current']['confirmed'])
        self.assertEqual(w2.total_expected_export_value, na_data_2017[
                         'values']['non_hvc']['current']['unconfirmed'])

    def test_5_non_hvc_win_in_overview_confirmed_2016_for_2016(self):
        num_to_create = 5
        for i in range(num_to_create):
            self._create_non_hvc_win(
                win_date=self.frozen_date, export_value=self.export_value, confirm=True, country='CA', fin_year=2016)

        # should not be in 2017
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        self.assertEqual(
            0,
            s("sum([?name=='North America'].values.*.current[].[confirmed,unconfirmed][])", data_2017)
        )

        # should show up in 2016
        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        na_data_2016 = s("[?name=='North America']|[0]", data_2016)
        self.assertEqual(self.export_value * num_to_create,
                         na_data_2016['values']['non_hvc']['current']['confirmed'])

    def test_overview_non_hvc_1_unconfirmed_last_year_should_show_up_in_new_region_if_country_has_moved_regions(self):
        w1 = self._create_non_hvc_win(win_date=self.frozen_date, confirm=False,
                                      fin_year=2016, export_value=self.export_value, country='CA')

        self.url = self.get_url_for_year(2016)
        data_2016 = self._api_response_data
        na_data_2016 = s("[?name=='North America']|[0]", data_2016)
        self.assertEqual(
            0,
            s("sum(values.non_hvc.current.[*][])", na_data_2016)
        )
        self.assertEqual(w1.country.code, 'CA')

        # move Canada to a different region
        region_year = OverseasRegionYear.objects.get(
            country__country='CA', financial_year_id=2017)
        region_year.overseas_region = OverseasRegion.objects.get(
            name='Western Europe')
        region_year.save()

        # it should be in this year
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        na_data_2017 = s("[?name=='North America']|[0]", data_2017)
        we_data_2017 = s("[?name=='Western Europe']|[0]", data_2017)

        self.assertEqual(0, na_data_2017['values'][
                         'non_hvc']['current']['unconfirmed'])
        self.assertEqual(w1.total_expected_export_value, we_data_2017[
                         'values']['non_hvc']['current']['unconfirmed'])


class OverseasRegionCampaignsTestCase(OverseasRegionBaseViewTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    view_base_url = reverse(
        'mi:overseas_region_campaigns', kwargs={"region_id": 1})

    def test_campaigns_list_2016(self):
        self.url = self.get_url_for_year(2016)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(
            api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(
            response_decoded["hvcs"]["campaigns"]))
        self.assertEqual(len(response_decoded["campaigns"]), 2)

    def test_campaigns_list_2017(self):
        self.url = self.get_url_for_year(2017)
        api_response = self._get_api_response(self.url)
        response_decoded = json.loads(
            api_response.content.decode("utf-8"))["results"]
        self.assertEqual(len(response_decoded["campaigns"]), len(
            response_decoded["hvcs"]["campaigns"]))
        self.assertEqual(len(response_decoded["campaigns"]), 8)


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class OverseasRegionDetailsTestCase(OverseasRegionBaseViewTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.export_value = 100000
        self.view_base_url = self.cen_region_url
        self.win_date_2017 = datetime.datetime(2017, 5, 25, tzinfo=get_current_timezone())
        self.win_date_2016 = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())
        self.fy_2016_last_date = datetime.datetime(2017, 3, 31, tzinfo=get_current_timezone())

    we_region_url = reverse('mi:overseas_region_detail', kwargs={"region_id": 5})
    cen_region_url = reverse('mi:overseas_region_detail', kwargs={"region_id": 10})
    region_url_2016_only = reverse('mi:overseas_region_detail', kwargs={"region_id": 15})
    region_url_2017_only = reverse('mi:overseas_region_detail', kwargs={"region_id": 18})

    def test_2017_region_in_2016_404(self):
        self.view_base_url = self.region_url_2017_only
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_region_in_2017_404(self):
        self.view_base_url = self.region_url_2016_only
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_details_no_wins_2016(self):
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["number"]["total"], 0)

        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

        self.assertEqual(api_response["wins"]["non_export"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["number"]["total"], 0)

    def test_details_no_wins_2017(self):
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["export"]["hvc"]["number"]["total"], 0)

        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

        self.assertEqual(api_response["wins"]["non_export"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["value"]["total"], 0)
        self.assertEqual(api_response["wins"]["non_export"]["number"]["total"], 0)

    def test_details_cen_hvc_win_for_2017_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=now(),
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 1)

    def test_details_cen_hvc_win_for_2017_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=now(),
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

    def test_details_cen_hvc_win_for_2016_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 1)

    def test_details_cen_hvc_win_for_2016_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

    def test_details_cen_hvc_win_confirmed_in_2016_appears_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 1)

    def test_details_cen_hvc_win_confirmed_in_2016_doesnt_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

    def test_details_cen_hvc_win_from_2016_confirmed_in_2017_doesnt_appears_in_2016(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

    def test_details_cen_hvc_win_from_2016_confirmed_in_2017_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 1)

    def test_details_hvc_win_from_other_region_but_cen_country_doesnt_appear_in_cen(self):
        self._create_hvc_win(
            hvc_code='E016',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

    def test_details_hvc_win_from_other_region_other_country_doesnt_appear_in_cen(self):
        self._create_hvc_win(
            hvc_code='E016',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='CA'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

    def test_details_cen_hvc_win_unconfirmed_in_2016_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 1)

    def test_details_cen_hvc_win_unconfirmed_in_2017_appears_in_2017(self):
        self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 0)

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["hvc"]["number"]["total"], 1)

    def test_details_unconfirmed_hvc_win_last_year_should_show_up_in_new_region_if_country_has_moved_regions(self):
        w1 = self._create_hvc_win(
            hvc_code='E017',
            win_date=self.win_date_2016,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        # check in CEN first
        self.view_base_url = self.cen_region_url
        self.url = self.get_url_for_year(2017)
        data_2016 = self._api_response_data
        self.assertEqual(data_2016["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(data_2016["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(data_2016["wins"]["export"]["hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(data_2016["wins"]["export"]["hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(data_2016["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(data_2016["wins"]["export"]["hvc"]["number"]["total"], 1)

        # move HU to a different region
        region_year = OverseasRegionYear.objects.get(
            country__country='HU', financial_year_id=2017)
        region_year.overseas_region = OverseasRegion.objects.get(
            name='Western Europe')
        region_year.save()

        # it should be in within Western Europe region this year
        self.view_base_url = self.we_region_url
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        self.assertEqual(data_2017["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(data_2017["wins"]["export"]["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(data_2017["wins"]["export"]["hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(data_2017["wins"]["export"]["hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(data_2017["wins"]["export"]["hvc"]["value"]["total"], self.export_value)
        self.assertEqual(data_2017["wins"]["export"]["hvc"]["number"]["total"], 1)

    # Non-HVC
    def test_details_cen_non_hvc_win_for_2017_in_2017(self):
        self._create_non_hvc_win(
            win_date=now(),
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 1)

    def test_details_cen_non_hvc_win_for_2017_in_2016(self):
        self._create_non_hvc_win(
            win_date=now(),
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

    def test_details_cen_non_hvc_win_for_2016_in_2016(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 1)

    def test_details_cen_non_hvc_win_for_2016_in_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

    def test_details_cen_non_hvc_win_confirmed_in_2016_appears_in_2016(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 1)

    def test_details_cen_non_hvc_win_confirmed_in_2016_doesnt_appears_in_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

    def test_details_cen_non_hvc_win_from_2016_confirmed_in_2017_doesnt_appears_in_2016(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

    def test_details_cen_non_hvc_win_from_2016_confirmed_in_2017_appears_in_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 1)

    def test_details_non_hvc_win_from_other_region_other_country_doesnt_appear_in_cen(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='CA'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

    def _test_details_non_hvc_win_from_cen_region_other_country_doesnt_appear_in_cen(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='CA'
        )
        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

    def test_details_cen_non_hvc_win_unconfirmed_in_2016_appears_in_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 1)

    def test_details_cen_non_hvc_win_unconfirmed_in_2017_appears_in_2017(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2016)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 0)

        self.url = self.get_url_for_year(2017)
        cen_response = self._api_response_data
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(cen_response["wins"]["export"]["non_hvc"]["number"]["total"], 1)

    def test_details_unconfirmed_non_hvc_win_last_year_should_show_up_in_new_region_if_country_has_moved_regions(self):
        w1 = self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='HU'
        )
        # check in CEN first
        self.view_base_url = self.cen_region_url
        self.url = self.get_url_for_year(2017)
        data_2016 = self._api_response_data
        self.assertEqual(data_2016["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(data_2016["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(data_2016["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(data_2016["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(data_2016["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(data_2016["wins"]["export"]["non_hvc"]["number"]["total"], 1)

        # move HU to a different region
        region_year = OverseasRegionYear.objects.get(
            country__country='HU', financial_year_id=2017)
        region_year.overseas_region = OverseasRegion.objects.get(
            name='Western Europe')
        region_year.save()

        # it should be in within Western Europe region this year
        self.view_base_url = self.we_region_url
        self.url = self.get_url_for_year(2017)
        data_2017 = self._api_response_data
        self.assertEqual(data_2017["wins"]["export"]["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(data_2017["wins"]["export"]["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(data_2017["wins"]["export"]["non_hvc"]["value"]["unconfirmed"], self.export_value)
        self.assertEqual(data_2017["wins"]["export"]["non_hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(data_2017["wins"]["export"]["non_hvc"]["value"]["total"], self.export_value)
        self.assertEqual(data_2017["wins"]["export"]["non_hvc"]["number"]["total"], 1)
