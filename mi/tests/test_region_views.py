import datetime

from django.utils.timezone import now, get_current_timezone
from unittest import mock

from factory.fuzzy import FuzzyDate
from freezegun import freeze_time
from jmespath import search as s

from django.urls import reverse
from django.core.management import call_command

from fixturedb.factories.win import create_win_factory
from mi.models import OverseasRegionGroup, OverseasRegion, FinancialYear, OverseasRegionGroupYear, OverseasRegionYear
from mi.tests.base_test_case import MiApiViewsBaseTestCase, MiApiViewsWithWinsBaseTestCase
from mi.utils import sort_campaigns_by
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
    export_value = 100000
    win_date_2017 = datetime.datetime(2017, 5, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())
    fy_2016_last_date = datetime.datetime(2017, 3, 31, tzinfo=get_current_timezone())

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)

    def assert_result_count(self, expected_length):
        self.assertEqual(
            expected_length,
            len(self._api_response_data)
        )

    @property
    def countries(self):
        return {x['name'].lower() for x in self._api_response_data}


class OverseasRegionListViewTestCase(OverseasRegionBaseViewTestCase):
    view_base_url = reverse('mi:overseas_regions')

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


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class OverseasRegionCampaignsTestCase(OverseasRegionBaseViewTestCase):
    list_regions_base_url = reverse('mi:overseas_regions')
    view_base_url = reverse('mi:overseas_region_campaigns', kwargs={"region_id": 10})
    CEN_16_HVCS = ["E017", "E018", "E019", "E020",]
    CEN_17_HVCS = ["E017", "E018", "E019", "E020", "E219", "E220", "E221", "E222",]
    TEST_CAMPAIGN_ID = "E017"
    TARGET_E017 = 30000000
    PRORATED_TARGET = 2465760  # target based on the frozen date

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.url = self.get_url_for_year(2017)

    def test_campaigns_list_2016(self):
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(
            api_response["hvcs"]["campaigns"]))
        self.assertEqual(len(api_response["campaigns"]), 4)

    def test_campaigns_2016_no_duplicates(self):
        list_regions_url = self.get_url_for_year(year=2016,
                                                 base_url=self.list_regions_base_url)
        all_regions = self._get_api_response(list_regions_url).data["results"]
        for region in all_regions:
            region_url = reverse('mi:overseas_region_campaigns',
                                 kwargs={"region_id": region["id"]})
            self.url = self.get_url_for_year(2016, base_url=region_url)
            api_response = self._api_response_data
            for campaign in api_response["campaigns"]:
                dups = s("campaigns[?campaign_id=='{}'].campaign".format(campaign["campaign_id"]),
                         api_response)
                self.assertTrue(len(dups) == 1)

    def test_campaigns_list_2017(self):
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(
            api_response["hvcs"]["campaigns"]))
        self.assertEqual(len(api_response["campaigns"]), 8)

    def test_campaigns_list_2017_no_duplicates(self):
        list_regions_url = self.get_url_for_year(year=2017,
                                                 base_url=self.list_regions_base_url)
        all_regions = self._get_api_response(list_regions_url).data["results"]
        for region in all_regions:
            region_url = reverse('mi:overseas_region_campaigns',
                                 kwargs={"region_id": region["id"]})
            self.url = self.get_url_for_year(2017, base_url=region_url)
            api_response = self._api_response_data
            for campaign in api_response["campaigns"]:
                dups = s("campaigns[?campaign_id=='{}'].campaign".format(campaign["campaign_id"]),
                         api_response)
                self.assertTrue(len(dups) == 1)

    def test_campaigns_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "campaigns": [],
            "name": "Central European Network",
            "hvcs": {
                "campaigns": [
                    "HVC: E017",
                    "HVC: E018",
                    "HVC: E019",
                    "HVC: E020",
                ],
                "target": self.CAMPAIGN_TARGET * len(self.CEN_16_HVCS)
            },
            "avg_time_to_confirm": 0.0
        }
        campaigns = []
        for hvc_code in self.CEN_16_HVCS:
            campaigns.append({
                "campaign": "HVC",
                "campaign_id": hvc_code,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": 0,
                            "confirmed": 0,
                            "total": 0
                        },
                        "number": {
                            "unconfirmed": 0,
                            "confirmed": 0,
                            "total": 0
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": 0.0,
                        "confirmed_percent": 0.0,
                        "status": "red"
                    },
                    "target": self.CAMPAIGN_TARGET
                }
            })

        self.expected_response["campaigns"] = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        self.assertResponse()

    def test_avg_time_to_confirm_unconfirmed_wins(self):
        """ Average time to confirm will be zero, if there are no confirmed wins """
        for hvc_code in self.CEN_16_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=False)
        api_response = self._api_response_data
        expected_avg_time = 0.0
        response_avg_time = api_response["avg_time_to_confirm"]
        self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_nextday(self):
        """ Test average time to confirm when all wins confirmed in one day """
        for hvc_code in self.CEN_16_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                notify_date=self.win_date_2017,
                response_date=self.win_date_2017 + datetime.timedelta(days=1),
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )
        api_response = self._api_response_data
        expected_avg_time = 1.0
        response_avg_time = api_response["avg_time_to_confirm"]
        self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_randomly(self):
        """
        Average time to confirm should be more than one,
        when wins took more than one day to be confirmed
        """
        for hvc_code in self.CEN_16_HVCS:
            response_date = FuzzyDate(datetime.datetime(2017, 5, 27),
                                      datetime.datetime(2017, 5, 31)).evaluate(2, None, False)
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                notify_date=self.win_date_2017,
                response_date=response_date,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        api_response = self._api_response_data
        response_avg_time = api_response["avg_time_to_confirm"]
        self.assertTrue(response_avg_time > 1.0)

    def test_campaigns_count_no_wins(self):
        """ Make sure number of campaigns returned have no effect when there are no wins """
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(self.CEN_17_HVCS))

    def test_campaigns_count_unconfirmed_wins(self):
        """ unconfirmed wins shouldn't have any effect on number of campaigns """
        for hvc_code in self.CEN_16_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(self.CEN_17_HVCS))

    def test_campaigns_count_confirmed_wins(self):
        """ confirmed HVC wins shouldn't have any effect on number of campaigns """
        for hvc_code in self.CEN_16_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )

        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(self.CEN_17_HVCS))

    def test_campaigns_count_unconfirmed_nonhvc_wins(self):
        """ unconfirmed non-hvc wins shouldn't have any effect on number of campaigns """
        for _ in self.CEN_16_HVCS:
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(self.CEN_17_HVCS))

    def test_campaigns_count_confirmed_nonhvc_wins(self):
        """ unconfirmed non-hvc wins shouldn't have any effect on number of campaigns """
        for _ in self.CEN_16_HVCS:
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(self.CEN_17_HVCS))

    def test_campaign_progress_colour_no_wins(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are no wins """
        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_unconfirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are no confirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=100000,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_confirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are not enough confirmed wins """
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=100000,
            country='HU'
        )
        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_nonhvc_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are only non-hvc wins """
        for _ in range(1, 11):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=100000,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_nonhvc_confirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=100000,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_confirmed_wins_amber(self):
        """
        Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        export_val = self.PRORATED_TARGET * 30 / 100
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=export_val,
            country='HU'
        )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "amber")

    def test_campaign_progress_confirmed_wins_50_green(self):
        """ Progress colour should be green if there are enough win to take runrate past 45% """
        for _ in range(1, 5):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=3000000,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "green")

    def test_campaign_progress_confirmed_wins_45_green(self):
        """ Boundary Testing for Green:
        Progress colour should be green if there are enough win to take runrate past 45% """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=791700,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "green")

    def test_campaign_progress_confirmed_wins_44_amber(self):
        """
        Boundary testing for Amber: Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        export_val = self.PRORATED_TARGET * 44 / 100
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=export_val/10,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "amber")

    def test_campaign_progress_confirmed_wins_25_amber(self):
        """
        Boundary testing for Amber: Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        export_val = self.PRORATED_TARGET * 25 / 100
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=export_val/10,
                country='HU'
            )
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID, export_value=146700, confirm=True)

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "amber")

    def test_campaign_progress_confirmed_wins_24_red(self):
        """ Boundary testing for red: Anything less than 25% runrate of progress should be Red """
        export_val = self.PRORATED_TARGET * 24 / 100
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=export_val/10,
                country='HU'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_percent_no_wins(self):
        """ Progress percentage will be 0, if there are no confirmed HVC wins """
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_unconfirmed_wins(self):
        """ Progress percentage will be 0, if there are no confirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10.0)

    def test_campaign_progress_percent_confirmed_wins_1(self):
        """ Test simple progress percent """
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=300000,
            country='HU'
        )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 1.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_nonhvc_wins(self):
        """ Non hvc wins shouldn't effect progress percent """
        for _ in range(1, 11):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=100000,
                country='HU'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_nonhvc_confirmed_wins(self):
        """ Non hvc confirmed wins shouldn't effect progress percent """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_confirmed_wins_20(self):
        """ Check 20% progress percent """
        for _ in range(1, 3):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=3000000,
                country='HU'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 20.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_hvc_number_no_wins(self):
        """ HVC number shouldn't be affected when there are no wins """
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_number_only_nonhvc_wins(self):
        """ HVC number shouldn't be affected when there are only non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_number_only_nonhvc_confirmed_wins(self):
        """ HVC number shouldn't be affected when there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_number_unconfirmed_wins(self):
        """ Check HVC number with unconfirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)

    def test_campaign_hvc_number_confirmed_wins(self):
        """ Check HVC number with confirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)

    def test_campaign_hvc_number_mixed_wins(self):
        """ Check HVC numbers with both confirmed and unconfirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 20)

    def test_campaign_hvc_value_no_wins(self):
        """ HVC value will be 0 with there are no wins """
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_value_only_nonhvc_wins(self):
        """ HVC value will be 0 there are only unconfirmed non-HVC wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_value_only_nonhvc_confirmed_wins(self):
        """ HVC value will be 0 when there are only confirmed non-HVC wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_value_unconfirmed_wins(self):
        """ Check HVC value when there are unconfirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)

    def test_campaign_hvc_value_confirmed_wins(self):
        """ Check HVC value when there are confirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)

    def test_campaign_hvc_value_mixed_wins(self):
        """ Check HVC value when there are both confirmed and unconfirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='HU'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 6000000)


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
        self.view_base_url = self.cen_region_url

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
        self._create_hvc_win(
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
        self._create_non_hvc_win(
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
