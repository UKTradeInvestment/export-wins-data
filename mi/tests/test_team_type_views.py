import datetime
from django.core.management import call_command
from django.urls import reverse

from django.utils.timezone import get_current_timezone
from freezegun import freeze_time

from fixturedb.factories.win import create_win_factory
from mi.tests.base_test_case import MiApiViewsWithWinsBaseTestCase
from mi.tests.utils import GenericTopNonHvcWinsTestMixin, GenericWinTableTestMixin


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
