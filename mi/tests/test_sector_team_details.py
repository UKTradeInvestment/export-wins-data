import datetime

from django.core.management import call_command
from django.core.urlresolvers import reverse

from freezegun import freeze_time

from mi.tests.base_test_case import MiApiViewsBaseTestCase
from mi.tests.test_sector_views import SectorTeamBaseTestCase
from wins.factories import (
    CustomerResponseFactory,
    NotificationFactory,
)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamDetailViewsTestCase(SectorTeamBaseTestCase):
    """
    Tests covering SectorTeam overview and detail API endpoints
    """

    view_base_url = reverse('mi:sector_team_detail', kwargs={'team_id': 1})
    url = reverse('mi:sector_team_detail', kwargs={'team_id': 1}) + "?year=2016"
    expected_response = {}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        # initialise for every test
        self.expected_response = {
            "wins": {
                "export": {
                    "hvc": {
                        "value": {
                            "confirmed": 0,
                            "unconfirmed": 0,
                            "total": 0
                        },
                        "number": {
                            "confirmed": 0,
                            "unconfirmed": 0,
                            "total": 0
                        }
                    },
                    "non_hvc": {
                        "value": {
                            "confirmed": 0,
                            "unconfirmed": 0,
                            "total": 0
                        },
                        "number": {
                            "confirmed": 0,
                            "unconfirmed": 0,
                            "total": 0
                        }
                    },
                    "totals": {
                        "number": {
                            "confirmed": 0,
                            "unconfirmed": 0,
                            "grand_total": 0
                        },
                        "value": {
                            "confirmed": 0,
                            "unconfirmed": 0,
                            "grand_total": 0
                        }
                    },
                },
                "non_export": {
                    "value": {
                        "confirmed": 0,
                        "unconfirmed": 0,
                        "total": 0
                    },
                    "number": {
                        "confirmed": 0,
                        "unconfirmed": 0,
                        "total": 0
                    }
                }
            },
            "name": "Financial & Professional Services",
            "hvcs": {
                "campaigns": [
                    "HVC: E006",
                    "HVC: E019",
                    "HVC: E031",
                    "HVC: E072",
                    "HVC: E095",
                    "HVC: E115",
                    "HVC: E128",
                    "HVC: E160",
                    "HVC: E167",
                    "HVC: E191"
                ],
                "target": self.CAMPAIGN_TARGET * len(self.TEAM_1_HVCS)
            },
            "avg_time_to_confirm": 0.0
        }

    def get_url_for_year(self, year):
        return '{base}?year={year}'.format(base=self.view_base_url, year=year)

    def test_no_sector_team(self):
        no_sector_url = reverse('mi:sector_team_detail', kwargs={'team_id': 100}) + "?year=2016"
        no_sector_expected_response = {
            "error": "team not found"
        }
        no_sector_api_response = self._get_api_response(no_sector_url, 400)
        self.assertJSONEqual(no_sector_api_response.content.decode("utf-8"), no_sector_expected_response)

    def test_sector_team_detail_1_unconfirmed_wins(self):
        """ SectorTeam Details with unconfirmed HVC wins, all wins on same day """
        for i in range(5):
            self._create_hvc_win()

        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 500000
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 5

        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    def test_sector_team_detail_1_confirmed_wins(self):
        """ SectorTeam Details with confirmed HVC wins, all wins on same day """
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))

        self.expected_response['wins']['export']['hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 500000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 5

        self.expected_response['wins']['non_export']['value']['confirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['confirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_unconfirmed_wins_from_last_fy_in_current_fy(self):
        """ Make sure unconfirmed wins from last FY are accounted for in current FY """
        # create few confirmed wins last FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))
        # create few unconfirmed wins from last FY
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 1))
        # create few confirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2017, 4, 1),
                                 notify_date=datetime.datetime(2017, 4, 1),
                                 response_date=datetime.datetime(2017, 4, 10))
        # create few unconfirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2017, 4, 1))

        self.url = self.get_url_for_year(2017)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['confirmed'], 5)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['unconfirmed'], 1000000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['unconfirmed'], 10)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['total'], 1500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['total'], 15)

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_unconfirmed_wins_from_last_fy_in_last_fy(self):
        """ Make sure unconfirmed wins from last FY are not accounted for in last FY """
        # create few confirmed wins last FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))
        # create few unconfirmed wins from last FY
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 1))
        # create few confirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2017, 4, 1),
                                 notify_date=datetime.datetime(2017, 4, 1),
                                 response_date=datetime.datetime(2017, 4, 10))
        # create few unconfirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2017, 4, 1))

        self.url = self.get_url_for_year(2016)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['confirmed'], 5)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['unconfirmed'], 0)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['unconfirmed'], 0)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['total'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['total'], 5)

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_no_unconfirmed_wins_from_older_than_12_months_1(self):
        """ Make sure unconfirmed wins from last FY that are older than 12 months are not accounted for this FY """
        # create few confirmed wins last FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))
        # create few unconfirmed wins from last FY May
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 1))
        # create few confirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2017, 4, 1),
                                 notify_date=datetime.datetime(2017, 4, 1),
                                 response_date=datetime.datetime(2017, 4, 10))
        # create few unconfirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2017, 4, 1))

        self.url = self.get_url_for_year(2017)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['confirmed'], 5)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['unconfirmed'], 1000000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['unconfirmed'], 10)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['total'], 1500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['total'], 15)

        # once its past May 2017, previous year's unconfirmed wins that are older than 12 months,
        # should be ignored
        with freeze_time(datetime.datetime(2017, 6, 1)):
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['confirmed'], 5)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['unconfirmed'], 500000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['unconfirmed'], 5)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['total'], 1000000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['total'], 10)

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_no_unconfirmed_wins_from_older_than_12_months_2(self):
        """
        Make sure unconfirmed wins from last FY that are older than 12 months are not accounted for this FY
        Boundary testing
        """
        # create few confirmed wins last FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))
        # create few unconfirmed wins from last FY April/May
        self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 4, 21))
        self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 1))
        self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 2))
        # create few confirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2017, 4, 1),
                                 notify_date=datetime.datetime(2017, 4, 1),
                                 response_date=datetime.datetime(2017, 4, 10))
        # create few unconfirmed wins this FY
        for i in range(5):
            self._create_hvc_win(confirm=False, win_date=datetime.datetime(2017, 4, 1))

        self.url = self.get_url_for_year(2017)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['confirmed'], 5)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['unconfirmed'], 700000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['unconfirmed'], 7)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['total'], 1200000)
        self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['total'], 12)

        # once its past May 2017, previous year's unconfirmed wins that are older than 12 months,
        # should be ignored
        with freeze_time(datetime.datetime(2017, 5, 2)):
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['confirmed'], 500000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['confirmed'], 5)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['unconfirmed'], 600000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['unconfirmed'], 6)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['value']['total'], 1100000)
            self.assertEqual(self._api_response_data['wins']['export']['hvc']['number']['total'], 11)

    def test_sector_team_detail_1_hvc_nonhvc_unconfirmed(self):
        """ SectorTeam Details with unconfirmed wins both HVC and non-HVC, all wins on same day """
        for i in range(5):
            self._create_hvc_win()

        for i in range(5):
            self._create_non_hvc_win()

        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['non_hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['non_hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['non_hvc']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['non_hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 0
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 1000000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 1000000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 0
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 10
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 10

        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    def test_sector_team_detail_1_nonhvc_empty_hvc(self):
        """ SectorTeam Details with unconfirmed wins non-HVC, where HVC is empty string instead of None """
        for i in range(5):
            self._create_non_hvc_win()

        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 0
        self.expected_response['wins']['export']['hvc']['value']['total'] = 0
        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 0
        self.expected_response['wins']['export']['hvc']['number']['total'] = 0

        self.expected_response['wins']['export']['non_hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['non_hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['non_hvc']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['non_hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 0
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 500000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 0
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 5

        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 0
        self.expected_response['wins']['non_export']['value']['total'] = 0
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 0
        self.expected_response['wins']['non_export']['number']['total'] = 0

        self.assertResponse()

    def test_sector_team_detail_1_hvc_nonhvc_confirmed(self):
        """ SectorTeam Details with confirmed wins both HVC and non-HVC, all wins on same day """
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))

        for i in range(5):
            self._create_non_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                     notify_date=datetime.datetime(2016, 5, 1),
                                     response_date=datetime.datetime(2016, 5, 1))

        self.expected_response['wins']['export']['hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['non_hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['non_hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['non_hvc']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['non_hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 1000000
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 0
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 1000000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 10
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 0
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 10

        self.expected_response['wins']['non_export']['value']['confirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['confirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    def test_sector_team_detail_1_hvc_nonhvc_confirmed_unconfirmed(self):
        """ SectorTeam Details with confirmed wins both HVC and non-HVC, all wins on same day """
        for i in range(5):
            self._create_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 2),
                                 response_date=datetime.datetime(2016, 5, 2))

        for i in range(5):
            self._create_non_hvc_win(confirm=True, win_date=datetime.datetime(2016, 5, 1),
                                     notify_date=datetime.datetime(2016, 5, 2),
                                     response_date=datetime.datetime(2016, 5, 2))

        for i in range(5):
            self._create_hvc_win()

        for i in range(5):
            self._create_non_hvc_win()

        self.expected_response['wins']['export']['hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['confirmed'] = 5

        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 5

        self.expected_response['wins']['export']['hvc']['value']['total'] = 1000000
        self.expected_response['wins']['export']['hvc']['number']['total'] = 10

        self.expected_response['wins']['export']['non_hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['non_hvc']['number']['confirmed'] = 5

        self.expected_response['wins']['export']['non_hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['non_hvc']['number']['unconfirmed'] = 5

        self.expected_response['wins']['export']['non_hvc']['value']['total'] = 1000000
        self.expected_response['wins']['export']['non_hvc']['number']['total'] = 10

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 1000000
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 1000000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 2000000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 10
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 10
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 20

        self.expected_response['wins']['non_export']['value']['confirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 23000
        self.expected_response['wins']['non_export']['number']['confirmed'] = 5
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 10

        self.assertResponse()

    def test_sector_team_detail_1_nonhvc_unconfirmed(self):
        """ SectorTeam Details with unconfirmed non-HVC wins, all wins on same day """
        self._create_non_hvc_win(sector_id=58)

        self.expected_response['wins']['export']['non_hvc']['value']['unconfirmed'] = 100000
        self.expected_response['wins']['export']['non_hvc']['value']['total'] = 100000
        self.expected_response['wins']['export']['non_hvc']['number']['unconfirmed'] = 1
        self.expected_response['wins']['export']['non_hvc']['number']['total'] = 1

        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 100000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 100000
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 1
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 1

        self.assertResponse()

    def test_sector_team_detail_1_nonhvc_confirmed(self):
        """ SectorTeam Details with confirmed non-HVC wins, all wins on same day """
        self._create_non_hvc_win(confirm=True, sector_id=58, win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 1),
                                 response_date=datetime.datetime(2016, 5, 1))

        self.expected_response['wins']['export']['non_hvc']['value']['confirmed'] = 100000
        self.expected_response['wins']['export']['non_hvc']['value']['total'] = 100000
        self.expected_response['wins']['export']['non_hvc']['number']['confirmed'] = 1
        self.expected_response['wins']['export']['non_hvc']['number']['total'] = 1

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 100000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 100000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 1
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 1

        self.assertResponse()

    def test_sector_team_detail_1_average_time_to_confirm(self):
        """ Add one confirmed HVC win and check avg_time_to_confirm value """
        self._create_hvc_win(confirm=True,
                             win_date=datetime.datetime(2016, 5, 1),
                             notify_date=datetime.datetime(2016, 5, 2),
                             response_date=datetime.datetime(2016, 5, 3))

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 1.0)

    def test_sector_team_detail_1_non_hvc_average_time_to_confirm(self):
        """ Add one confirmed non-HVC win and check avg_time_to_confirm value """
        self._create_non_hvc_win(confirm=True)

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 1.0)

    def test_sector_team_detail_1_average_time_to_confirm_multiple_wins(self):
        """ Add few wins, HVC and non-HVC with different dates - no duplicates
        Confirm some of those wins with varying confirmation dates
        Check avg_time_to_confirm value """

        for d in [3, 4, 5, 6]:
            self._create_hvc_win(confirm=True,
                                 win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 2),
                                 response_date=datetime.datetime(2016, 5, d))

        # add a hvc win without confirmation
        self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 1))
        for i in range(3):
            self._create_non_hvc_win(win_date=datetime.datetime(2016, 5, 1))

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 2.5)

    def test_sector_team_detail_1_average_time_to_confirm_multiple_duplicate_wins_1(self):
        """ Add few HVC wins, Add multiple notifications with different dates.
        Confirm those wins with varying confirmation dates
        Check avg_time_to_confirm value, wins with multiple notifications shouldn't be considered
        only the earliest notification is considered while calculating average confirmation time """

        days = [3, 4, 5, 6]

        for day in days:
            self._create_hvc_win(confirm=True,
                                 win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 2),
                                 response_date=datetime.datetime(2016, 5, day))

        # add multiple notifications, for E006 but one customer response
        win = self._create_hvc_win(hvc_code='E006', win_date=datetime.datetime(2016, 5, 1))
        for day in days:
            notification1 = NotificationFactory(win=win)
            notification1.created = datetime.datetime(2016, 5, day)
            notification1.save()
        response1 = CustomerResponseFactory(win=win, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 6)
        response1.save()

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 2.6)

    def test_sector_team_detail_1_average_time_to_confirm_multiple_duplicate_wins_2(self):
        """ Add few HVC wins, Add multiple notifications with different dates.
        Confirm those wins with varying confirmation dates
        Also add few more wins without any confirmation.
        Check avg_time_to_confirm value, wins with multiple notifications shouldn't be considered
        and wins without any confirmation shouldn't be considered either
        only the earliest notification is considered while calculating average confirmation time """

        days = [3, 4, 5, 6]

        for day in days:
            self._create_hvc_win(confirm=True,
                                 win_date=datetime.datetime(2016, 5, 1),
                                 notify_date=datetime.datetime(2016, 5, 2),
                                 response_date=datetime.datetime(2016, 5, day))

        # add multiple notifications, for E006 but one customer response
        win = self._create_hvc_win(hvc_code='E006', win_date=datetime.datetime(2016, 5, 1))
        for day in days:
            notification1 = NotificationFactory(win=win)
            notification1.created = datetime.datetime(2016, 5, day)
            notification1.save()
        response1 = CustomerResponseFactory(win=win, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 6)
        response1.save()

        # add few random hvc wins without confirmation
        self._create_hvc_win(confirm=False, win_date=datetime.datetime(2016, 5, 1))
        for i in range(3):
            self._create_non_hvc_win(win_date=datetime.datetime(2016, 5, 1))

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 2.6)

    def test_sector_team_detail_1_average_time_to_confirm_no_wins(self):
        """
        avg_time_to_confirm should be 0.0 when there are no wins, not error.
        """
        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 0.0)
