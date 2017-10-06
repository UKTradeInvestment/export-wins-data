from unittest.mock import PropertyMock

from django.db.models import Q
from unittest import mock

import datetime
from django.core.management import call_command
from django.test import tag, TestCase, SimpleTestCase
from django.urls import reverse
from django.utils.text import slugify

from django.utils.timezone import get_current_timezone
from freezegun import freeze_time
from jmespath import search as s

from fixturedb.factories.win import create_win_factory
from mi.views.team_type_views import BaseTeamTypeMIView
from mi.views.ukregion_views import UKRegionWinsFilterMixin, UKRegionTeamTypeNameMixin, UKRegionValidOptionsMixin
from wins.constants import HQ_TEAM_REGION_OR_POST, UK_REGIONS
from wins.factories import AdvisorFactory
from mi.tests.base_test_case import MiApiViewsWithWinsBaseTestCase
from mi.tests.utils import GenericTopNonHvcWinsTestMixin, GenericWinTableTestMixin, GenericDetailsTestMixin, \
    GenericCampaignsViewTestCase, GenericMonthlyViewTestCase


@freeze_time(MiApiViewsWithWinsBaseTestCase.frozen_date_17)
class TeamTypeBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):
    TEST_TEAM = 'post:Albania - Tirana'
    TEAM_TYPE = 'post'
    TEST_TEAM_NAME = TEST_TEAM.lstrip(f'{TEAM_TYPE}:')
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)

    export_value = 100000
    win_date_2017 = datetime.datetime(
        2017, 4, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(
        2016, 5, 25, tzinfo=get_current_timezone())
    fy_2016_last_date = datetime.datetime(
        2017, 3, 31, tzinfo=get_current_timezone())

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)


class PostTopNonHVCViewTestCase(TeamTypeBaseViewTestCase, GenericTopNonHvcWinsTestMixin):

    export_value = 9992

    post_top_nonhvc_url = reverse('mi:posts_top_nonhvc', kwargs={
                                  "team_slug": "albania-tirana"})
    post_topnonhvc_url_invalid = reverse(
        'mi:posts_top_nonhvc', kwargs={"team_slug": "ABC"})
    post_topnonhvc_url_missing_post_kwarg = reverse(
        'mi:posts_top_nonhvc', kwargs={"team_slug": None})

    fin_years = [2016, 2017]

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='post',
            default_hq_team='post:Albania - Tirana'
        )
        self.view_base_url = self.post_top_nonhvc_url

    def test_fake_post_404(self):
        self.view_base_url = self.post_topnonhvc_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_missing_post_404(self):
        self.view_base_url = self.post_topnonhvc_url_missing_post_kwarg
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)


class PostWinTableTestCase(TeamTypeBaseViewTestCase, GenericWinTableTestMixin):

    TEST_COUNTRY_CODE = 'IE'
    fin_years = [2016, 2017]

    expected_response = {
        "post": {
            "id": "albania-tirana",
            "name": "Albania - Tirana",
        },
        "avg_time_to_confirm": 0.0,
        "wins": {
            "hvc": [],
        }
    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='post',
            default_hq_team='post:Albania - Tirana'
        )
        self.post_win_table_url = reverse('mi:post_win_table', kwargs={
            'team_slug': 'albania-tirana'
        })
        self.post_win_table_url_invalid = reverse('mi:post_win_table', kwargs={
            'team_slug': 'notalbania-tirana'
        })
        self.view_base_url = self.post_win_table_url


class PostListViewTestCase(TeamTypeBaseViewTestCase):
    view_base_url = reverse('mi:post')

    def test_list_of_posts(self):
        self.url = self.get_url_for_year(2016)
        response_data = self._api_response_data

        # must be a subset of the full HQ_TEAM_REGION_OR_POST
        self.assertTrue(len(response_data) <= len(HQ_TEAM_REGION_OR_POST))

        # must be same length as the HQ_TEAM_REGION_OR_POST list filtered by team type
        self.assertEqual(
            len(response_data),
            len({k: v for k, v in HQ_TEAM_REGION_OR_POST if k.startswith('post')})
        )

        self.assertEqual(set(response_data[0].keys()), {'id', 'name'})

        # year doesn't matter
        self.expected_response = response_data
        self.url = self.get_url_for_year(2017)
        self.assertResponse()


class PostDetailViewTestCase(TeamTypeBaseViewTestCase, GenericDetailsTestMixin):

    TEST_TEAM = 'post:Albania - Tirana'
    TEAM_TYPE = 'post'
    TEST_TEAM_NAME = TEST_TEAM.lstrip(f'{TEAM_TYPE}:')
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='post',
            default_hq_team=self.TEST_TEAM
        )
        self.post_detail_url = reverse('mi:post_detail', kwargs={
            'team_slug': self.TEST_TEAM_SLUG
        })
        self.post_detail_url_invalid = reverse('mi:post_detail', kwargs={
            'team_slug': 'notalbania-tirana'
        })
        self.post_detail_url_missing_post_kwarg = reverse(
            'mi:post_detail', kwargs={"team_slug": None})
        self.view_base_url = self.post_detail_url

        self.expected_response = dict(
            id=self.TEST_TEAM_SLUG,
            name='Albania - Tirana',
            **self.expected_response
        )

    def test_fake_post_detail_404(self):
        self.view_base_url = self.post_detail_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_missing_post_detail_404(self):
        self.view_base_url = self.post_detail_url_missing_post_kwarg
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_detail_wrong_post_doesnt_appear_in_albania(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE,
            hq_team="post:Austria - Vienna"
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assert_no_wins_no_values(api_response)

    def assert_top_level_keys(self, response_data):
        subset = {
            'name': self.TEST_TEAM_NAME,
            'id': self.TEST_TEAM_SLUG
        }
        self.assertDictContainsSubset(subset, response_data)


class PostCampaignsViewTestCase(TeamTypeBaseViewTestCase, GenericCampaignsViewTestCase):
    TEST_TEAM = 'post:Albania - Tirana'
    TEAM_TYPE = 'post'
    TEST_TEAM_NAME = TEST_TEAM.lstrip(f'{TEAM_TYPE}:')
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)
    CEN_16_HVCS = ["E045", "E046", "E047", "E048", "E214"]
    CEN_17_HVCS = ["E045", "E046", "E047", "E054", "E119", "E225"]
    TEST_CAMPAIGN_ID = "E045"
    TARGET_E017 = 10000000
    PRORATED_TARGET = 833333  # target based on the frozen date

    view_base_url = reverse('mi:posts_campaigns', kwargs={
                            'team_slug': TEST_TEAM_SLUG})

    expected_response = {
        "campaigns": [],
        "name": TEST_TEAM_NAME,
        "id": TEST_TEAM_SLUG,
        "hvcs": {
            "campaigns": [],
            "target": 0
        },
        "avg_time_to_confirm": 0.0
    }

    def setUp(self):
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='post',
            default_hq_team=self.TEST_TEAM
        )

    def test_campaigns_count_no_wins(self):
        """
        In Posts view the campaigns are generated from the
        wins themselves. So if there are no wins there should be no
        campaigns
        """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                api_response = self._api_response_data
                self.assertEqual(len(api_response["campaigns"]), 0)

    def test_campaign_progress_colour_1_win(self):
        """
        Given the 'Frozen datetime', progress colour will be zero if there is 1 win.
        For the posts view it'll always be 'zero'
        """
        self._create_hvc_win(
            win_date=self.win_date_2017,
            hvc_code=self.TEST_CAMPAIGN_ID,
            confirm=True,
            fin_year=2017,
            export_value=1,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        e017_status = s(f"campaigns[?campaign_id=='{self.TEST_CAMPAIGN_ID}'].totals.progress.status",
                        api_response)[0]
        self.assertEqual(e017_status, "zero")

    def test_campaign_progress_colour_10_wins(self):
        """
        Given the 'Frozen datetime', progress colour will be zero if there are no wins.
        For the posts view it'll always be 'zero'
        """
        for _ in range(10):
            self._create_hvc_win(
                win_date=self.win_date_2017,
                hvc_code=self.TEST_CAMPAIGN_ID,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        e017_status = s(f"campaigns[?campaign_id=='{self.TEST_CAMPAIGN_ID}'].totals.progress.status",
                        api_response)[0]
        self.assertEqual(e017_status, "zero")

    def test_campaign_progress_percent_confirmed_wins_1(self):
        """
        Test simple progress percent
        """
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self.url = self.get_url_for_year(year)
                self._create_hvc_win(
                    hvc_code=self.TEST_CAMPAIGN_ID,
                    win_date=win_date,
                    confirm=True,
                    fin_year=2017,
                    export_value=self.export_value,
                    country=self.TEST_COUNTRY_CODE
                )
                api_response = self._api_response_data
                # progress should always be 0
                self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                                   .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
                self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                                   .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)


class PostMonthsViewTestCase(TeamTypeBaseViewTestCase, GenericMonthlyViewTestCase):

    TEST_TEAM = 'post:Albania - Tirana'
    TEAM_TYPE = 'post'
    TEST_TEAM_NAME = TEST_TEAM.lstrip(f'{TEAM_TYPE}:')
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)

    view_base_url = reverse('mi:posts_months', kwargs={
                            'team_slug': TEST_TEAM_SLUG})
    expected_response = {
        "campaigns": [],
        "name": TEST_TEAM_NAME,
        "id": TEST_TEAM_SLUG,
        "hvcs": {
            "campaigns": [],
            "target": 0
        },
        "avg_time_to_confirm": 0.0
    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type=self.TEAM_TYPE,
            default_hq_team=self.TEST_TEAM
        )


@tag('uk_region')
class UKRegionTopNonHVCViewTestCase(TeamTypeBaseViewTestCase, GenericTopNonHvcWinsTestMixin):

    export_value = 9992

    uk_region_top_nonhvc_url = reverse('mi:uk_regions_top_nonhvc', kwargs={
                                       "team_slug": "south-west"})
    uk_region_topnonhvc_url_invalid = reverse(
        'mi:uk_regions_top_nonhvc', kwargs={"team_slug": "ABC"})
    uk_region_topnonhvc_url_missing_uk_region_kwarg = reverse(
        'mi:uk_regions_top_nonhvc', kwargs={"team_slug": None})

    fin_years = [2016, 2017]

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='itt',
            default_hq_team='itt:DIT South West'
        )
        self.view_base_url = self.uk_region_top_nonhvc_url

    def test_fake_post_404(self):
        self.view_base_url = self.uk_region_topnonhvc_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_missing_post_404(self):
        self.view_base_url = self.uk_region_topnonhvc_url_missing_uk_region_kwarg
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)


@tag('uk_region')
class UKRegionWinTableTestCase(TeamTypeBaseViewTestCase, GenericWinTableTestMixin):

    TEST_COUNTRY_CODE = 'IE'
    fin_years = [2016, 2017]

    expected_response = {
        "uk_region": {
            "id": "south-west",
            "name": "South West",
        },
        "avg_time_to_confirm": 0.0,
        "wins": {
            "hvc": [],
        }
    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='itt',
            default_hq_team='itt:DIT South West'
        )
        self.uk_region_win_table_url = reverse('mi:uk_regions_win_table', kwargs={
            'team_slug': 'south-west'
        })
        self.uk_region_win_table_url_invalid = reverse('mi:uk_regions_win_table', kwargs={
            'team_slug': 'notsouth-west'
        })
        self.view_base_url = self.uk_region_win_table_url


@tag('uk_region')
class UKRegionListViewTestCase(TeamTypeBaseViewTestCase):
    view_base_url = reverse('mi:uk_regions')

    def test_list_of_uk_regions(self):
        self.url = self.get_url_for_year(2016)
        response_data = self._api_response_data

        # must be same length as the UK_REGIONS
        self.assertEqual(
            len(response_data),
            len(UK_REGIONS)
        )

        self.assertEqual(set(response_data[0].keys()), {
                         'id', 'name', 'target'})

        # year doesn't matter
        self.expected_response = response_data
        self.url = self.get_url_for_year(2017)
        self.assertResponse()


@tag('uk_region')
class UKRegionDetailViewTestCase(TeamTypeBaseViewTestCase, GenericDetailsTestMixin):

    TEST_TEAM = 'south-west'
    TEAM_TYPE = 'uk_region'
    TEST_TEAM_NAME = "South West"
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)

    expected_response = {
        **GenericDetailsTestMixin.expected_response,
        "name": TEST_TEAM_NAME,
        "id": TEST_TEAM_SLUG,
        'target': None,
        "avg_time_to_confirm": 0.0,
        'export_experience': {'total': {'number': {'confirmed': 0,
                                                   'total': 0,
                                                   'unconfirmed': 0},
                                        'value': {'confirmed': 0,
                                                  'total': 0,
                                                  'unconfirmed': 0}}},
    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='itt',
            default_hq_team='itt:DIT South West'
        )
        self.uk_region_detail_url = reverse('mi:uk_regions_detail', kwargs={
            'team_slug': self.TEST_TEAM_SLUG
        })
        self.uk_region_detail_url_invalid = reverse('mi:uk_regions_detail', kwargs={
            'team_slug': 'notsouth-west'
        })
        self.uk_region_detail_url_missing_uk_region_kwarg = reverse(
            'mi:uk_regions_detail', kwargs={"team_slug": None})
        self.view_base_url = self.uk_region_detail_url

        self.expected_response = dict(
            **self.expected_response
        )

    def test_fake_uk_region_detail_404(self):
        self.view_base_url = self.uk_region_detail_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_missing_uk_region_detail_404(self):
        self.view_base_url = self.uk_region_detail_url_missing_uk_region_kwarg
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_detail_wrong_uk_region_doesnt_appear_in_south_west(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE,
            hq_team="itt:DIT Team East"
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assert_no_wins_no_values(api_response)

    def assert_top_level_keys(self, response_data):
        subset = {
            'name': self.TEST_TEAM_NAME,
            'id': self.TEST_TEAM_SLUG
        }
        self.assertDictContainsSubset(subset, response_data)

    def test_detail_hvc_win_appear_in_south_west(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE,
            hq_team="itt:DIT South West"
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 1)

    def test_detail_non_hvc_win_appear_in_south_west(self):
        win = self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE,
        )
        win.team_type = 'itt'
        win.hq_team = "itt:DIT South West"
        win.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["confirmed"], 1)

    def test_detail_non_hvc_win_appear_in_south_west_even_with_diff_contributor(self):
        win = self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE,
        )
        win.team_type = 'itt'
        win.hq_team = "itt:DIT South West"
        win.save()

        AdvisorFactory(
            win=win,
            name='UKTI SW',
            team_type='itt',
            hq_team="itt:DIT North West"
        )

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["confirmed"], 1)

    def test_non_hvc_win_by_north_west_but_contributed_by_south_west_appear_in_south_west(self):
        win = self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        win.team_type = 'itt'
        win.hq_team = 'itt:DIT North West'
        win.save()
        AdvisorFactory(
            win=win,
            name='UKTI SW',
            team_type='itt',
            hq_team="itt:DIT South West"
        )
        # check south-west
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["confirmed"], 1)


@tag('uk_region')
class UKRegionCampaignsViewTestCase(TeamTypeBaseViewTestCase, GenericCampaignsViewTestCase):
    TEST_TEAM = 'itt:DIT South West'
    TEAM_TYPE = 'itt'
    TEST_TEAM_NAME = "South West"
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)
    CEN_16_HVCS = ["E045", "E046", "E047", "E048", "E214"]
    CEN_17_HVCS = ["E045", "E046", "E047", "E054", "E119", "E225"]
    TEST_CAMPAIGN_ID = "E045"
    TARGET_E017 = 10000000
    PRORATED_TARGET = 833333  # target based on the frozen date

    view_base_url = reverse('mi:uk_regions_campaigns', kwargs={
        'team_slug': TEST_TEAM_SLUG})

    expected_response = {
        "campaigns": [],
        'hvcs': {'campaigns': [], 'target': 0},
        "name": TEST_TEAM_NAME,
        "id": TEST_TEAM_SLUG,
        "avg_time_to_confirm": 0.0,

    }

    def setUp(self):
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type='itt',
            default_hq_team=self.TEST_TEAM
        )

    def test_campaigns_count_no_wins(self):
        """
        In Posts view the campaigns are generated from the
        wins themselves. So if there are no wins there should be no
        campaigns
        """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                api_response = self._api_response_data
                self.assertEqual(len(api_response["campaigns"]), 0)

    def test_campaign_progress_colour_1_win(self):
        """
        Given the 'Frozen datetime', progress colour will be zero if there is 1 win.
        For the posts view it'll always be 'zero'
        """
        self._create_hvc_win(
            win_date=self.win_date_2017,
            hvc_code=self.TEST_CAMPAIGN_ID,
            confirm=True,
            fin_year=2017,
            export_value=1,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        e017_status = s(f"campaigns[?campaign_id=='{self.TEST_CAMPAIGN_ID}'].totals.progress.status",
                        api_response)[0]
        self.assertEqual(e017_status, "zero")

    def test_campaign_progress_colour_10_wins(self):
        """
        Given the 'Frozen datetime', progress colour will be zero if there are no wins.
        For the posts view it'll always be 'zero'
        """
        for _ in range(10):
            self._create_hvc_win(
                win_date=self.win_date_2017,
                hvc_code=self.TEST_CAMPAIGN_ID,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        e017_status = s(f"campaigns[?campaign_id=='{self.TEST_CAMPAIGN_ID}'].totals.progress.status",
                        api_response)[0]
        self.assertEqual(e017_status, "zero")

    def test_campaign_progress_percent_confirmed_wins_1(self):
        """
        Test simple progress percent
        """
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self.url = self.get_url_for_year(year)
                self._create_hvc_win(
                    hvc_code=self.TEST_CAMPAIGN_ID,
                    win_date=win_date,
                    confirm=True,
                    fin_year=2017,
                    export_value=self.export_value,
                    country=self.TEST_COUNTRY_CODE
                )
                api_response = self._api_response_data
                # progress should always be 0
                self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                                   .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
                self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                                   .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)


@tag('uk_region')
class UKRegionsMonthsViewTestCase(TeamTypeBaseViewTestCase, GenericMonthlyViewTestCase):

    TEST_TEAM = 'itt:DIT South West'
    TEAM_TYPE = 'itt'
    TEST_TEAM_NAME = "South West"
    TEST_TEAM_SLUG = slugify(TEST_TEAM_NAME)

    view_base_url = reverse('mi:uk_regions_months', kwargs={
        'team_slug': TEST_TEAM_SLUG})
    expected_response = {
        "campaigns": [],
        "name": TEST_TEAM_NAME,
        "id": TEST_TEAM_SLUG,
        'target': {'target': None},
        "avg_time_to_confirm": 0.0,
        'export_experience': {'total': {'number': {'confirmed': 0,
                                                   'total': 0,
                                                   'unconfirmed': 0},
                                        'value': {'confirmed': 0,
                                                  'total': 0,
                                                  'unconfirmed': 0}}},
    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS,
            default_team_type=self.TEAM_TYPE,
            default_hq_team=self.TEST_TEAM
        )


# Test UK Region Mixins, these are more important than the above test
# as they materially change the functionality of the underlying base
# class. The above tests only test configuration changes produce the
# correct behaviour


@tag('uk_region', 'mixin')
class UKRegionWinsFilterMixinTestCase(SimpleTestCase):

    def test_team_filter_is_called_instead_of_base(self):

        # check that base class property is called
        with mock.patch('mi.views.team_type_views.BaseTeamTypeMIView._team_filter', return_value='whocares', new_callable=PropertyMock) as mocked:
            test_base_instance = BaseTeamTypeMIView()
            test_base_instance.team_type = 'itt'
            mocked.assert_not_called()

            class Test(UKRegionWinsFilterMixin, BaseTeamTypeMIView):
                team_type = 'uk_regions'
                team_slug = 'south-west'

                team = {'id': 9, 'slug': 'south-west'}

            test_derived_instance = Test()
            ret = test_derived_instance._team_filter
            # base class still not called
            mocked.assert_not_called()

    def test_team_filter_with_1_team_in_group_returns_1_team(self):

        class Test1(UKRegionWinsFilterMixin, BaseTeamTypeMIView):
            team_type = 'uk_regions'
            team_slug = 'south-west'

            team = {'id': 9, 'slug': 'south-west'}

        test_derived_instance = Test1()
        ret = test_derived_instance._team_filter

        # is a django orm filter
        self.assertTrue(isinstance(ret, Q))

        # that three is only 1 filter
        self.assertEqual(len(ret.children), 1)

        # selected teams are the ones we expect
        team_ids = ret.children[0][1]
        self.assertListEqual(team_ids, ['itt:DIT South West'])

    def test_team_filter_with_multiple_teams_in_group_returns_1_team(self):

        class Test2(UKRegionWinsFilterMixin, BaseTeamTypeMIView):
            team_type = 'uk_regions'
            team_slug = 'yorkshire-and-the-humber'

            team = {'id': 12, 'slug': 'yorkshire-and-the-humber'}

        test_derived_instance = Test2()
        ret = test_derived_instance._team_filter

        # is a django orm filter
        self.assertTrue(isinstance(ret, Q))

        # that three is only 1 filter
        self.assertEqual(len(ret.children), 1)

        # selected teams are the ones we expect
        team_ids = ret.children[0][1]
        self.assertListEqual(
            team_ids,
            [
                'itt:DIT Yorkshire',
                'itt:DIT Yorkshire and Humber Regional Sector Specialists'
            ]
        )


@tag('uk_region', 'mixin')
class UKRegionTeamTypeNameMixinTestCase(SimpleTestCase):

    def test_team_name(self):
        test_team_type_literal = 'itt'
        test_base_instance = BaseTeamTypeMIView()
        test_base_instance.team_type = test_team_type_literal
        self.assertEqual(test_base_instance.team_type_key,
                         test_base_instance.team_type)

        class Test(UKRegionTeamTypeNameMixin, BaseTeamTypeMIView):
            team_type = test_team_type_literal
            team_slug = 'south-west'

        test_derived_instance = Test()
        self.assertNotEqual(test_derived_instance.team_type_key,
                            test_base_instance.team_type_key)
        self.assertNotEqual(test_derived_instance.team_type_key,
                            test_derived_instance.team_type)
        self.assertEqual(test_derived_instance.team_type_key, 'uk_region')


@tag('uk_region', 'mixin')
class UKRegionValidOptionsMixinTestCase(SimpleTestCase):

    def test_valid_options_returns_uk_regions_not_iit_teams(self):

        test_team_type_literal = 'itt'
        test_base_instance = BaseTeamTypeMIView()
        test_base_instance.team_type = test_team_type_literal

        class Test(UKRegionValidOptionsMixin, BaseTeamTypeMIView):
            team_type = test_team_type_literal
            team_slug = 'south-west'

        test_derived_instance = Test()
        self.assertNotEqual(test_base_instance.valid_options,
                            test_derived_instance.valid_options)
        self.assertEqual(
            {x['name'] for x in test_derived_instance.valid_options},
            set(UK_REGIONS.displays.keys())
        )
