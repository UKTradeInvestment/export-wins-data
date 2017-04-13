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
class SectorTeamDetailViewsTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering SectorTeam overview and detail API endpoints
    """

    url = reverse('mi:sector_team_detail', kwargs={'team_id': 1}) + "?year=2016"
    expected_response = {}

    def setUp(self):
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
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), sector=FuzzyChoice(self.TEAM_1_SECTORS))

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
            win = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), confirmed=True,
                             sector=FuzzyChoice(self.TEAM_1_SECTORS))
            CustomerResponseFactory(win=win, agree_with_win=True)

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

    def test_sector_team_detail_1_hvc_nonhvc_unconfirmed(self):
        """ SectorTeam Details with unconfirmed wins both HVC and non-HVC, all wins on same day """
        for i in range(5):
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), sector=FuzzyChoice(self.TEAM_1_SECTORS))

        for i in range(5):
            WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(self.TEAM_1_SECTORS))

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
            WinFactory(user=self.user, hvc='', sector=FuzzyChoice(self.TEAM_1_SECTORS))

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
            hvc_win = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS),
                                 sector=FuzzyChoice(self.TEAM_1_SECTORS))
            CustomerResponseFactory(win=hvc_win, agree_with_win=True)

        for i in range(5):
            non_hvc_win = WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(self.TEAM_1_SECTORS))
            CustomerResponseFactory(win=non_hvc_win, agree_with_win=True)

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
            hvc_win = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS),
                                 sector=FuzzyChoice(self.TEAM_1_SECTORS))
            CustomerResponseFactory(win=hvc_win, agree_with_win=True)

        for i in range(5):
            non_hvc_win = WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(self.TEAM_1_SECTORS))
            CustomerResponseFactory(win=non_hvc_win, agree_with_win=True)

        for i in range(5):
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), sector=FuzzyChoice(self.TEAM_1_SECTORS))

        for i in range(5):
            WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(self.TEAM_1_SECTORS))

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
        WinFactory(user=self.user, hvc=None, sector=58)

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
        win = WinFactory(user=self.user, hvc=None, sector=58)
        CustomerResponseFactory(win=win, agree_with_win=True)

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
        win1 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(self.TEAM_1_SECTORS))
        notification1 = NotificationFactory(win=win1)
        notification1.created = datetime.datetime(2016, 5, 2)
        notification1.save()
        response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 3)
        response1.save()

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 1.0)

    def test_sector_team_detail_1_non_hvc_average_time_to_confirm(self):
        """ Add one confirmed non-HVC win and check avg_time_to_confirm value """
        win1 = WinFactory(user=self.user, hvc=None, date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(self.TEAM_1_SECTORS))
        notification1 = NotificationFactory(win=win1)
        notification1.created = datetime.datetime(2016, 5, 2)
        notification1.save()
        response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 3)
        response1.save()

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 1.0)

    def test_sector_team_detail_1_average_time_to_confirm_multiple_wins(self):
        """ Add few wins, HVC and non-HVC with different dates - no duplicates
        Confirm some of those wins with varying confirmation dates
        Check avg_time_to_confirm value """

        win1 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(self.TEAM_1_SECTORS))
        notification1 = NotificationFactory(win=win1)
        notification1.created = datetime.datetime(2016, 5, 2)
        notification1.save()
        response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 3)
        response1.save()

        win2 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(self.TEAM_1_SECTORS))
        notification2 = NotificationFactory(win=win2)
        notification2.created = datetime.datetime(2016, 5, 2)
        notification2.save()
        response2 = CustomerResponseFactory(win=win2, agree_with_win=True)
        response2.created = datetime.datetime(2016, 5, 4)
        response2.save()

        win3 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(self.TEAM_1_SECTORS))
        notification3 = NotificationFactory(win=win3)
        notification3.created = datetime.datetime(2016, 5, 2)
        notification3.save()
        response3 = CustomerResponseFactory(win=win3, agree_with_win=True)
        response3.created = datetime.datetime(2016, 5, 5)
        response3.save()

        win4 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(self.TEAM_1_SECTORS))
        notification4 = NotificationFactory(win=win4)
        notification4.created = datetime.datetime(2016, 5, 2)
        notification4.save()
        response4 = CustomerResponseFactory(win=win4, agree_with_win=True)
        response4.created = datetime.datetime(2016, 5, 6)
        response4.save()

        # add a hvc win without confirmation
        WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                   sector=FuzzyChoice(self.TEAM_1_SECTORS))
        for i in range(3):
            WinFactory(user=self.user, hvc=None, date=datetime.datetime(2016, 5, 1),
                       sector=FuzzyChoice(self.TEAM_1_SECTORS))

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 2.5)

    def test_sector_team_detail_1_average_time_to_confirm_multiple_duplicate_wins_1(self):
        """ Add few HVC wins, Add multiple notifications with different dates.
        Confirm those wins with varying confirmation dates
        Check avg_time_to_confirm value, wins with multiple notifications shouldn't be considered
        only the earliest notification is considered while calculating average confirmation time """

        days = [3, 4, 5, 6]

        for day in days:
            win1 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                              sector=FuzzyChoice(self.TEAM_1_SECTORS))
            notification1 = NotificationFactory(win=win1)
            notification1.created = datetime.datetime(2016, 5, 2)
            notification1.save()
            response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
            response1.created = datetime.datetime(2016, 5, day)
            response1.save()

        # add multiple notifications, for E006 but one customer response
        win = WinFactory(user=self.user, hvc='E006', date=datetime.datetime(2016, 5, 1),
                         sector=FuzzyChoice(self.TEAM_1_SECTORS))
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
            win1 = WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                              sector=FuzzyChoice(self.TEAM_1_SECTORS))
            notification1 = NotificationFactory(win=win1)
            notification1.created = datetime.datetime(2016, 5, 2)
            notification1.save()
            response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
            response1.created = datetime.datetime(2016, 5, day)
            response1.save()

        # add multiple notifications, for E006 but one customer response
        win = WinFactory(user=self.user, hvc='E006', date=datetime.datetime(2016, 5, 1),
                         sector=FuzzyChoice(self.TEAM_1_SECTORS))
        for day in days:
            notification1 = NotificationFactory(win=win)
            notification1.created = datetime.datetime(2016, 5, day)
            notification1.save()
        response1 = CustomerResponseFactory(win=win, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 6)
        response1.save()

        # add few random hvc wins without confirmation
        WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                   sector=FuzzyChoice(self.TEAM_1_SECTORS))
        for i in range(3):
            WinFactory(user=self.user, hvc=None, date=datetime.datetime(2016, 5, 1),
                       sector=FuzzyChoice(self.TEAM_1_SECTORS))

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 2.6)

    def test_sector_team_detail_1_average_time_to_confirm_no_wins(self):
        """
        avg_time_to_confirm should be 0.0 when there are no wins, not error.
        """
        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 0.0)
