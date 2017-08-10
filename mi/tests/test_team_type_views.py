import datetime
from django.core.management import call_command
from django.urls import reverse
from django.utils.text import slugify

from django.utils.timezone import get_current_timezone
from freezegun import freeze_time

from fixturedb.factories.win import create_win_factory
from wins.constants import HQ_TEAM_REGION_OR_POST
from mi.tests.base_test_case import MiApiViewsWithWinsBaseTestCase
from mi.tests.utils import GenericTopNonHvcWinsTestMixin, GenericWinTableTestMixin, GenericDetailsTestMixin


@freeze_time(MiApiViewsWithWinsBaseTestCase.frozen_date_17)
class TeamTypeBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):
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

    post_top_nonhvc_url = reverse('mi:posts_top_nonhvc', kwargs={"team_slug": "albania-tirana"})
    post_topnonhvc_url_invalid = reverse('mi:posts_top_nonhvc', kwargs={"team_slug": "ABC"})
    post_topnonhvc_url_missing_post_kwarg = reverse('mi:posts_top_nonhvc', kwargs={"team_slug": None})

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
            "id": "post:Albania - Tirana",
            "name": "Albania - Tirana",
            "slug": "albania-tirana",
        },
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

        self.assertEqual(set(response_data[0].keys()), {'slug', 'id', 'name'})

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
        self.post_detail_url_missing_post_kwarg = reverse('mi:post_detail', kwargs={"team_slug": None})
        self.view_base_url = self.post_detail_url

        self.expected_response = dict(
            id=self.TEST_TEAM,
            name='Albania - Tirana',
            slug=self.TEST_TEAM_SLUG,
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
            'slug': self.TEST_TEAM_SLUG,
            'id': self.TEST_TEAM
        }
        self.assertDictContainsSubset(subset, response_data)
