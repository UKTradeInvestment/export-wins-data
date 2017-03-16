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
from wins.models import HVC

GROUP_4_HVCS = ['E001', 'E017', 'E024', 'E049', 'E063', 'E107', 'E184']
TEAM_SECTORS = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
GROUP_4_TARGET = 70000000
HVC_TARGET = 10000000


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupListTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering HVCGroup overview API endpoints
    """

    url = reverse('mi:hvc_groups')

    def test_hvc_group_list(self):
        """ test `HVCGroup` list API """

        self.expected_response = sorted([
            {
                "name": "Advanced Manufacturing",
                "id": 1
            },
            {
                "name": "Advanced Manufacturing - Marine",
                "id": 2
            },
            {
                "name": "Aerospace",
                "id": 3
            },
            {
                "name": "Automotive",
                "id": 4
            },
            {
                "name": "Bio-economy - Agritech",
                "id": 5
            },
            {
                "name": "Bio-economy - Chemicals",
                "id": 6
            },
            {
                "name": "Consumer Goods & Retail",
                "id": 7
            },
            {
                "name": "Creative Industries",
                "id": 8
            },
            {
                "name": "Defence",
                "id": 9
            },
            {
                "name": "Digital Economy",
                "id": 10
            },
            {
                "name": "Education",
                "id": 11
            },
            {
                "name": "Energy - Nuclear",
                "id": 12
            },
            {
                "name": "Energy - Offshore Wind",
                "id": 13
            },
            {
                "name": "Energy - Oil & Gas",
                "id": 14
            },
            {
                "name": "Energy - Renewables",
                "id": 15
            },
            {
                "name": "Financial Services",
                "id": 16
            },
            {
                "name": "Food & Drink",
                "id": 17
            },
            {
                "name": "Healthcare",
                "id": 18
            },
            {
                "name": "Infrastructure - Aid Funded Business",
                "id": 19
            },
            {
                "name": "Infrastructure - Airports",
                "id": 20
            },
            {
                "name": "Infrastructure - Construction",
                "id": 21
            },
            {
                "name": "Infrastructure - Mining",
                "id": 22
            },
            {
                "name": "Infrastructure - Rail",
                "id": 23
            },
            {
                "name": "Infrastructure - Water",
                "id": 24
            },
            {
                "name": "Life Sciences",
                "id": 25
            },
            {
                "name": "Professional Services",
                "id": 26
            },
            {
                "name": "Sports Economy",
                "id": 27
            },
            {
                "name": "Strategic Campaigns",
                "id": 28
            }
        ], key=lambda x: (x['name']))
        self.assertResponse()


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupDetailTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering HVC Group details API endpoint
    """

    url = reverse('mi:hvc_group_detail', kwargs={'group_id': 4})
    expected_response = {}

    def setUp(self):
        self.expected_response = {
            "hvcs": {
                "target": GROUP_4_TARGET,
                "campaigns": [
                    "HVC: E001",
                    "HVC: E017",
                    "HVC: E024",
                    "HVC: E049",
                    "HVC: E063",
                    "HVC: E107",
                    "HVC: E184"
                ]
            },
            "avg_time_to_confirm": 0.0,
            "wins": {
                "export": {
                    "totals": {
                        "value": {
                            "grand_total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "number": {
                            "grand_total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    },
                    "hvc": {
                        "value": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "number": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    }
                },
                "non_export": {
                    "value": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "number": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                }
            },
            "name": "Automotive"
        }

    def test_hvc_group_detail_unconfirmed_wins(self):
        """ test `HVCGroup` detail API with few unconfirmed wins """
        for i in range(5):
            WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))

        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 5
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 500000

        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5
        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000

        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    def test_hvc_group_detail_1_confirmed_wins(self):
        """ `HVCGroup` Details with confirmed HVC wins, all wins on same day """
        for i in range(5):
            win = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))
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

    def test_hvc_group_detail_1_hvc_nonhvc_unconfirmed(self):
        """
        `HVCGroup` Details with unconfirmed wins both HVC and non-HVC, all wins on same day

        None of the non-HVC wins will be considered when calculating wins for HVC Group
        """
        for i in range(5):
            WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))

        for i in range(5):
            WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(TEAM_SECTORS))

        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 0
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 500000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 0
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 5

        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    def test_hvc_group_detail_1_hvc_nonhvc_confirmed(self):
        """
        `HVCGroup` Details with confirmed wins both HVC and non-HVC, all wins on same day

        None of the non-HVC wins will be considered when calculating wins for HVC Group
        """
        for i in range(5):
            hvc_win = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))
            CustomerResponseFactory(win=hvc_win, agree_with_win=True)

        for i in range(5):
            non_hvc_win = WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(TEAM_SECTORS))
            CustomerResponseFactory(win=non_hvc_win, agree_with_win=True)

        self.expected_response['wins']['export']['hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['value']['total'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['hvc']['number']['total'] = 5

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 0
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 500000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 0
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 5

        self.expected_response['wins']['non_export']['value']['confirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 11500
        self.expected_response['wins']['non_export']['number']['confirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 5

        self.assertResponse()

    def test_hvc_group_detail_1_hvc_nonhvc_confirmed_unconfirmed(self):
        """
        `HVCGroup` Details with confirmed wins both HVC and non-HVC, all wins on same day

        None of the non-HVC wins will be considered when calculating wins for HVC Group
        """
        for i in range(5):
            hvc_win = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))
            CustomerResponseFactory(win=hvc_win, agree_with_win=True)

        for i in range(5):
            non_hvc_win = WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(TEAM_SECTORS))
            CustomerResponseFactory(win=non_hvc_win, agree_with_win=True)

        for i in range(5):
            WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))

        for i in range(5):
            WinFactory(user=self.user, hvc=None, sector=FuzzyChoice(TEAM_SECTORS))

        self.expected_response['wins']['export']['hvc']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['confirmed'] = 5

        self.expected_response['wins']['export']['hvc']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['hvc']['number']['unconfirmed'] = 5

        self.expected_response['wins']['export']['hvc']['value']['total'] = 1000000
        self.expected_response['wins']['export']['hvc']['number']['total'] = 10

        self.expected_response['wins']['export']['totals']['value']['confirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['unconfirmed'] = 500000
        self.expected_response['wins']['export']['totals']['value']['grand_total'] = 1000000
        self.expected_response['wins']['export']['totals']['number']['confirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['unconfirmed'] = 5
        self.expected_response['wins']['export']['totals']['number']['grand_total'] = 10

        self.expected_response['wins']['non_export']['value']['confirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['unconfirmed'] = 11500
        self.expected_response['wins']['non_export']['value']['total'] = 23000
        self.expected_response['wins']['non_export']['number']['confirmed'] = 5
        self.expected_response['wins']['non_export']['number']['unconfirmed'] = 5
        self.expected_response['wins']['non_export']['number']['total'] = 10

        self.assertResponse()

    def test_hvc_group_detail_1_nonhvc_unconfirmed(self):
        """
        `HVCGroup` Details with unconfirmed non-HVC wins, all wins on same day

        Response will contain all 0s as None of the non-HVC wins will be considered when calculating wins for HVC Group
        """
        WinFactory(user=self.user, hvc=None, sector=58)

        self.assertResponse()

    def test_hvc_group_detail_1_nonhvc_confirmed(self):
        """
        `HVCGroup` Details with confirmed non-HVC wins, all wins on same day

        None of the non-HVC wins will be considered when calculating wins for HVC Group, even when they are confirmed
        """
        win = WinFactory(user=self.user, hvc=None, sector=58)
        CustomerResponseFactory(win=win, agree_with_win=True)

        self.assertResponse()

    def test_hvc_group_detail_1_average_time_to_confirm(self):
        """ Add one confirmed win and check avg_time_to_confirm value """
        win1 = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(TEAM_SECTORS))
        notification1 = NotificationFactory(win=win1)
        notification1.created = datetime.datetime(2016, 5, 2)
        notification1.save()
        response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 3)
        response1.save()

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 1.0)

    def test_hvc_group_detail_1_average_time_to_confirm_multiple_wins(self):
        """ Add few wins, HVC and non-HVC with different dates
        Confirm some of those wins with varying confirmation dates
        Check avg_time_to_confirm value """

        win1 = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(TEAM_SECTORS))
        notification1 = NotificationFactory(win=win1)
        notification1.created = datetime.datetime(2016, 5, 2)
        notification1.save()
        response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
        response1.created = datetime.datetime(2016, 5, 3)
        response1.save()

        win2 = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(TEAM_SECTORS))
        notification2 = NotificationFactory(win=win2)
        notification2.created = datetime.datetime(2016, 5, 2)
        notification2.save()
        response2 = CustomerResponseFactory(win=win2, agree_with_win=True)
        response2.created = datetime.datetime(2016, 5, 4)
        response2.save()

        win3 = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(TEAM_SECTORS))
        notification3 = NotificationFactory(win=win3)
        notification3.created = datetime.datetime(2016, 5, 2)
        notification3.save()
        response3 = CustomerResponseFactory(win=win3, agree_with_win=True)
        response3.created = datetime.datetime(2016, 5, 5)
        response3.save()

        win4 = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), date=datetime.datetime(2016, 5, 1),
                          sector=FuzzyChoice(TEAM_SECTORS))
        notification4 = NotificationFactory(win=win4)
        notification4.created = datetime.datetime(2016, 5, 2)
        notification4.save()
        response4 = CustomerResponseFactory(win=win4, agree_with_win=True)
        response4.created = datetime.datetime(2016, 5, 6)
        response4.save()

        WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), date=datetime.datetime(2016, 5, 1),
                   sector=FuzzyChoice(TEAM_SECTORS))
        for i in range(3):
            WinFactory(user=self.user, hvc=None, date=datetime.datetime(2016, 5, 1), sector=FuzzyChoice(TEAM_SECTORS))

        self.assertEqual(self._api_response_data['avg_time_to_confirm'], 2.5)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupCampaignViewsTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering `HVCGroup` Campaigns API endpoint
    """
    url = reverse('mi:hvc_group_campaigns', kwargs={'group_id': 4})

    expected_response = {}

    def setUp(self):
        self.expected_response = {
            "campaigns": [],
            "name": "Automotive",
            "hvcs": {
                "target": GROUP_4_TARGET,
                "campaigns": [
                    "HVC: E001",
                    "HVC: E017",
                    "HVC: E024",
                    "HVC: E049",
                    "HVC: E063",
                    "HVC: E107",
                    "HVC: E184"
                ]
            },
            "avg_time_to_confirm": 0.0
        }

    def test_sector_team_campaigns_1_wins_for_all_hvcs(self):
        """ Campaigns api for team 1, with wins for all HVCs """
        campaigns = []
        for hvc_code in GROUP_4_HVCS:
            win = WinFactory(user=self.user, hvc=hvc_code, sector=FuzzyChoice(TEAM_SECTORS))
            notification1 = NotificationFactory(win=win)
            notification1.created = datetime.datetime(2016, 5, 2)
            notification1.save()
            response1 = CustomerResponseFactory(win=win, agree_with_win=True)
            response1.created = datetime.datetime(2016, 5, 6)
            response1.save()

            campaigns.append({
                "campaign": HVC.objects.get(campaign_id=hvc_code).campaign,
                "campaign_id": hvc_code,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": 0,
                            "confirmed": 100000,
                            "total": 100000
                        },
                        "number": {
                            "unconfirmed": 0,
                            "confirmed": 1,
                            "total": 1
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": 0.0,
                        "confirmed_percent": 1.0,
                        "status": "red"
                    },
                    "target": HVC_TARGET
                }
            })

        self.expected_response["campaigns"] = campaigns
        self.expected_response["avg_time_to_confirm"] = 4.0

        self.assertJSONEqual(self._api_response_json, self.expected_response)

    def test_sector_team_campaigns_1_wins_for_all_hvcs_unconfirmed(self):
        """ Campaigns api for team 1, with wins for all HVCs"""
        campaigns = []
        for hvc_code in GROUP_4_HVCS:
            WinFactory(user=self.user, hvc=hvc_code)

            campaigns.append({
                "campaign": HVC.objects.get(campaign_id=hvc_code).campaign,
                "campaign_id": hvc_code,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": 100000,
                            "confirmed": 0,
                            "total": 100000
                        },
                        "number": {
                            "unconfirmed": 1,
                            "confirmed": 0,
                            "total": 1
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": 1.0,
                        "confirmed_percent": 0.0,
                        "status": "red"
                    },
                    "target": HVC_TARGET
                }
            })

        self.expected_response["campaigns"] = campaigns

        self.assertJSONEqual(self._api_response_json, self.expected_response)
