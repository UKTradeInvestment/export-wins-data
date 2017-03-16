import datetime

from django.core.urlresolvers import reverse
from factory.fuzzy import FuzzyChoice
from freezegun import freeze_time

from mi.tests.base_test_case import MiApiViewsBaseTestCase
from wins.factories import (
    CustomerResponseFactory,
    NotificationFactory,
    WinFactory,
)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamOverviewTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering Sector Team Overview API endpoint
    - hvc_target_values: current, target_percentage
    - confirmed_percent: hvc, non_hvc
    - hvc_performance: RAGZ
    - hvc_groups.hvc_performance: RAGZ
    - hvc_groups.hvc_target_values: current, target_percentage
    """
    expected_response = {}
    url = reverse('mi:sector_teams_overview')

    def _team_data(self, teams_list, id):
        """ returns specific team's data dict out of overview response list """
        team_data = next((team_item for team_item in teams_list if team_item["id"] == id), None)
        self.assertIsNotNone(team_data)
        return team_data

    def _create_win(self, hvc_code, sector_id=None, win_date=None, export_value=None,
                    confirm=False, notify_date=None, response_date=None):
        """ generic function creating `Win` """
        if not sector_id:
            sector_id = FuzzyChoice(self.TEAM_1_SECTORS)

        if not win_date:
            win_date = datetime.datetime(2016, 5, 25)

        win = WinFactory(user=self.user, hvc=hvc_code, sector=sector_id, date=win_date)

        if export_value:
            win.total_expected_export_value = export_value
            win.save()

        if confirm:
            if not notify_date:
                notify_date = datetime.datetime(2016, 5, 26)
            notification = NotificationFactory(win=win)
            notification.created = notify_date
            notification.save()
            if not response_date:
                response_date = datetime.datetime(2016, 5, 27)
            response = CustomerResponseFactory(win=win, agree_with_win=True)
            response.created = response_date
            response.save()

    def _create_hvc_win(self, hvc_code=None, sector_id=None, win_date=None, export_value=None,
                        confirm=False, notify_date=None, response_date=None):
        """ creates a dummy HVC `Win`, confirmed or unconfirmed """
        if not hvc_code:
            hvc_code = FuzzyChoice(self.TEAM_1_HVCS)

        self._create_win(hvc_code, sector_id, win_date, export_value, confirm, notify_date, response_date)

    def _create_non_hvc_win(self, sector_id=None, win_date=None, export_value=None,
                            confirm=False, notify_date=None, response_date=None):
        """ creates a dummy non-HVC `Win` using Factory, can be confirmed or unconfirmed """
        self._create_win(None, sector_id, win_date, export_value, confirm, notify_date, response_date)

    def test_hvc_target_values_no_wins(self):
        """
        When no wins, current export value must be 0
        and percentage must be 0 as well
        """
        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['current']['unconfirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_hvc_target_values_no_confirmed_hvc_wins(self):
        """
        When no confirmed HVC wins, current export value, which only considers confirmed HVC wins, must be 0
        Hence percentage must be 0 as well
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['current']['unconfirmed'], 1000000)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 1.0)

    def test_hvc_target_values_no_confirmed_non_hvc_wins(self):
        """
        When no confirmed Non-HVC wins, current export value, which only considers confirmed, must be 0
        Hence percentage must be 0 as well
        """
        for _ in range(10):
            self._create_non_hvc_win()

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['current']['unconfirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_hvc_target_values_confirmed_non_hvc_wins(self):
        """
        Even when there are confirmed wins that are non-HVC, current export value,
        which only considers confirmed HVC wins, must be 0
        Hence percentage must be 0 as well
        """
        for _ in range(10):
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['current']['unconfirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_hvc_target_values_confirmed_hvc_wins(self):
        """
        When there are confirmed HVC wins, current export value should be positively
        effected and percentage too
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, export_value=self.CAMPAIGN_TARGET, confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)
        current_value = target_value = self.CAMPAIGN_TARGET * len(self.TEAM_1_HVCS)

        self.assertEqual(team_1_data['values']['hvc']['current']['confirmed'], current_value)
        self.assertEqual(team_1_data['values']['hvc']['current']['unconfirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 100)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target'], target_value)

    def test_hvc_confirmed_percent_no_wins(self):
        """
        When no wins, both hvc and non-hvc confirmed percent will be 0
        """
        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_hvc_confirmed_percent_no_confirmed_hvc_wins(self):
        """
        When no confirmed HVC wins, confirmed percent for both hvc and non-hvc will be 0
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 1.0)

    def test_hvc_confirmed_percent_no_confirmed_non_hvc_wins(self):
        """
        When no confirmed Non-HVC wins, confirmed percent for both hvc and non-hvc will be 0
        """
        for _ in range(10):
            self._create_non_hvc_win()

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_hvc_confirmed_percent_confirmed_non_hvc_wins(self):
        """
        When there are confirmed wins that are non-HVC alone, confirmed percent for non-hvc is 100
        whereas hvc will be 0
        """
        for _ in range(10):
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_confirmed_percent_values_confirmed_hvc_wins(self):
        """
        When there are confirmed HVC wins, confirmed percent for hvc will be 100
        whereas non-hvc will be 0
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, export_value=self.CAMPAIGN_TARGET, confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['target_percent']['confirmed'], 100)
        self.assertEqual(team_1_data['values']['hvc']['target_percent']['unconfirmed'], 0)

    def test_confirmed_percent_values_confirmed_hvc_nonhvc_wins(self):
        """
        When there are equal amount of confirmed HVC and non-HVC wins,
        both hvc and non-hvc confirmed percent will be 50 each
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['hvc']['total_win_percent']['confirmed'], 50)
        self.assertEqual(team_1_data['values']['hvc']['total_win_percent']['unconfirmed'], 0)

    def test_non_hvc_target_values_no_wins(self):
        """
        When no wins, current export value must be 0
        and percentage must be 0 as well
        """
        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['current']['unconfirmed'], 0)

    def test_non_hvc_target_values_no_confirmed_hvc_wins(self):
        """
        When no confirmed HVC wins, current export value, which only considers confirmed non HVC wins,
        must be 0. Hence percentage must be 0 as well
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['current']['unconfirmed'], 0)

    def test_non_hvc_target_values_no_confirmed_non_hvc_wins(self):
        """
        When no confirmed Non-HVC wins, current export value, which only considers confirmed, must be 0
        Hence percentage must be 0 as well
        """
        for _ in range(10):
            self._create_non_hvc_win()

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['current']['unconfirmed'], 1000000)

    def test_non_hvc_target_values_confirmed_non_hvc_wins(self):
        """
        Even when there are confirmed wins that are non-HVC, current export value,
        which only considers confirmed HVC wins, must be 0
        Hence percentage must be 0 as well
        """
        for _ in range(10):
            self._create_non_hvc_win(export_value=self.CAMPAIGN_TARGET, confirm=True)

        current_value = target_value = self.CAMPAIGN_TARGET * 10
        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['current']['confirmed'], current_value)
        self.assertEqual(team_1_data['values']['non_hvc']['current']['unconfirmed'], 0)

    def test_non_hvc_target_values_confirmed_hvc_wins(self):
        """
        When there are confirmed HVC wins, current export value should be positively
        effected and percentage too
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, export_value=self.CAMPAIGN_TARGET, confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['current']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['current']['unconfirmed'], 0)

    def test_non_hvc_confirmed_percent_no_wins(self):
        """
        When no wins, both confirmed and unconfirmed percent will be 0
        """
        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['unconfirmed'], 0)

    def test_non_hvc_confirmed_percent_no_confirmed_hvc_wins(self):
        """
        When no confirmed non HVC wins, confirmed and unconfirmed percent for both non-hvc will be 0
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['unconfirmed'], 0)

    def test_non_hvc_confirmed_percent_no_confirmed_non_hvc_wins(self):
        """
        Bunch of unconfirmed Non-HVC wins, confirmed will be 0 with positive unconfirmed
        """
        for _ in range(10):
            self._create_non_hvc_win()

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['unconfirmed'], 100)

    def test_non_hvc_confirmed_percent_confirmed_non_hvc_wins(self):
        """
        When there are confirmed non HVC wins alone, confirmed percent for non-hvc is 100
        whereas unconfirmed will be 0
        """
        for _ in range(10):
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['confirmed'], 100)
        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['unconfirmed'], 0)

    def test_non_hvc_confirmed_percent_confirmed_hvc_wins(self):
        """
        When there are confirmed HVC wins, confirmed percent for hvc will be 100
        whereas non-hvc will be 0
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, export_value=self.CAMPAIGN_TARGET, confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['unconfirmed'], 0)

    def test_non_hvc_confirmed_percent_confirmed_hvc_nonhvc_wins(self):
        """
        When there are equal amount of confirmed HVC and non-HVC wins,
        both hvc and non-hvc confirmed percent will be 50 each
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['confirmed'], 50)
        self.assertEqual(team_1_data['values']['non_hvc']['total_win_percent']['unconfirmed'], 0)

    def test_totals_no_wins(self):
        """
        When no wins, both confirmed and unconfirmed totals will be 0
        """
        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['totals']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['totals']['unconfirmed'], 0)

    def test_totals_no_confirmed_hvc_wins(self):
        """
        When no confirmed non HVC and non hvc wins but few unconfirmed hvc wins,
        confirmed total will be 0 and unconfirmed total will be positive
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['totals']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['totals']['unconfirmed'], 1000000)

    def test_totals_no_confirmed_non_hvc_wins(self):
        """
        When no confirmed HVC and non HVC wins but few unconfirmed non HVC wins,
        confirmed total will be 0 and unconfirmed total will be positive
        """
        for _ in range(10):
            self._create_non_hvc_win()

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['totals']['confirmed'], 0)
        self.assertEqual(team_1_data['values']['totals']['unconfirmed'], 1000000)

    def test_totals_confirmed_non_hvc_wins(self):
        """
        when there are only few confirmed non HVC wins alone, confirmed total will be positive
        whereas unconfirmed total will be 0
        """
        for _ in range(10):
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['totals']['confirmed'], 1000000)
        self.assertEqual(team_1_data['values']['totals']['unconfirmed'], 0)

    def test_totals_confirmed_hvc_wins(self):
        """
        when there are only few confirmed HVC wins alone, confirmed total will be positive
        whereas unconfirmed total will be 0
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, export_value=self.CAMPAIGN_TARGET, confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['totals']['confirmed'], self.CAMPAIGN_TARGET * len(self.TEAM_1_HVCS))
        self.assertEqual(team_1_data['values']['totals']['unconfirmed'], 0)

    def test_totals_confirmed_hvc_nonhvc_wins(self):
        """
        When there are equal amount of confirmed HVC and non-HVC wins,
        both hvc and non-hvc confirmed percent will be 50 each
        """
        for hvc_code in self.TEAM_1_HVCS:
            self._create_hvc_win(hvc_code=hvc_code, confirm=True)
            self._create_non_hvc_win(confirm=True)

        api_response = self._get_api_response(self.url)
        team_1_data = self._team_data(api_response.data, 1)

        self.assertEqual(team_1_data['values']['totals']['confirmed'], 2000000)
        self.assertEqual(team_1_data['values']['totals']['unconfirmed'], 0)

    # further tests for sector team overview: values>totals, hvc_performance - specially zero target ones
