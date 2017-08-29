import datetime
import json

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.urls import NoReverseMatch
from django.utils.timezone import now, get_current_timezone

from factory.fuzzy import FuzzyChoice
from freezegun import freeze_time

from fixturedb.factories.win import create_win_factory
from mi.tests.base_test_case import MiApiViewsBaseTestCase, MiApiViewsWithWinsBaseTestCase
from mi.tests.utils import GenericWinTableTestMixin
from wins.factories import (
    CustomerResponseFactory,
    NotificationFactory,
    WinFactory,
)
from wins.models import HVC
from wins.models import Notification

GROUP_4_HVCS = [code + "16" for code in ["E001", "E017", "E024", "E049", "E063", "E107", "E184"]]
TEAM_SECTORS = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
GROUP_4_TARGET = 70000000
HVC_TARGET = 10000000
CAMPAIGNS = [
    "HVC: E001",
    "HVC: E017",
    "HVC: E024",
    "HVC: E049",
    "HVC: E063",
    "HVC: E107",
    "HVC: E184"
]


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupListTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering HVCGroup overview API endpoints
    """

    url = reverse("mi:hvc_groups") + "?year=2016"

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
        ], key=lambda x: (x["name"]))
        self.assertResponse()


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupDetailTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering HVC Group details API endpoint
    """

    url = reverse("mi:hvc_group_detail", kwargs={"group_id": 4}) + "?year=2016"
    expected_response = {}

    def setUp(self):
        self.expected_response = {
            "hvcs": {
                "target": GROUP_4_TARGET,
                "campaigns": CAMPAIGNS
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

        self.expected_response["wins"]["export"]["totals"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["export"]["totals"]["number"]["grand_total"] = 5
        self.expected_response["wins"]["export"]["totals"]["value"]["unconfirmed"] = 500000
        self.expected_response["wins"]["export"]["totals"]["value"]["grand_total"] = 500000

        self.expected_response["wins"]["export"]["hvc"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["export"]["hvc"]["number"]["total"] = 5
        self.expected_response["wins"]["export"]["hvc"]["value"]["unconfirmed"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["value"]["total"] = 500000

        self.expected_response["wins"]["non_export"]["value"]["unconfirmed"] = 11500
        self.expected_response["wins"]["non_export"]["value"]["total"] = 11500
        self.expected_response["wins"]["non_export"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["non_export"]["number"]["total"] = 5

        self.assertResponse()

    def test_hvc_group_detail_1_confirmed_wins(self):
        """ `HVCGroup` Details with confirmed HVC wins, all wins on same day """
        for i in range(5):
            win = WinFactory(user=self.user, hvc=FuzzyChoice(GROUP_4_HVCS), sector=FuzzyChoice(TEAM_SECTORS))
            CustomerResponseFactory(win=win, agree_with_win=True)

        self.expected_response["wins"]["export"]["hvc"]["value"]["confirmed"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["value"]["total"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["export"]["hvc"]["number"]["total"] = 5

        self.expected_response["wins"]["export"]["totals"]["value"]["confirmed"] = 500000
        self.expected_response["wins"]["export"]["totals"]["value"]["grand_total"] = 500000
        self.expected_response["wins"]["export"]["totals"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["export"]["totals"]["number"]["grand_total"] = 5

        self.expected_response["wins"]["non_export"]["value"]["confirmed"] = 11500
        self.expected_response["wins"]["non_export"]["value"]["total"] = 11500
        self.expected_response["wins"]["non_export"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["non_export"]["number"]["total"] = 5

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

        self.expected_response["wins"]["export"]["hvc"]["value"]["unconfirmed"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["value"]["total"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["export"]["hvc"]["number"]["total"] = 5

        self.expected_response["wins"]["export"]["totals"]["value"]["confirmed"] = 0
        self.expected_response["wins"]["export"]["totals"]["value"]["unconfirmed"] = 500000
        self.expected_response["wins"]["export"]["totals"]["value"]["grand_total"] = 500000
        self.expected_response["wins"]["export"]["totals"]["number"]["confirmed"] = 0
        self.expected_response["wins"]["export"]["totals"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["export"]["totals"]["number"]["grand_total"] = 5

        self.expected_response["wins"]["non_export"]["value"]["unconfirmed"] = 11500
        self.expected_response["wins"]["non_export"]["value"]["total"] = 11500
        self.expected_response["wins"]["non_export"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["non_export"]["number"]["total"] = 5

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

        self.expected_response["wins"]["export"]["hvc"]["value"]["confirmed"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["value"]["total"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["export"]["hvc"]["number"]["total"] = 5

        self.expected_response["wins"]["export"]["totals"]["value"]["confirmed"] = 500000
        self.expected_response["wins"]["export"]["totals"]["value"]["unconfirmed"] = 0
        self.expected_response["wins"]["export"]["totals"]["value"]["grand_total"] = 500000
        self.expected_response["wins"]["export"]["totals"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["export"]["totals"]["number"]["unconfirmed"] = 0
        self.expected_response["wins"]["export"]["totals"]["number"]["grand_total"] = 5

        self.expected_response["wins"]["non_export"]["value"]["confirmed"] = 11500
        self.expected_response["wins"]["non_export"]["value"]["total"] = 11500
        self.expected_response["wins"]["non_export"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["non_export"]["number"]["total"] = 5

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

        self.expected_response["wins"]["export"]["hvc"]["value"]["confirmed"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["number"]["confirmed"] = 5

        self.expected_response["wins"]["export"]["hvc"]["value"]["unconfirmed"] = 500000
        self.expected_response["wins"]["export"]["hvc"]["number"]["unconfirmed"] = 5

        self.expected_response["wins"]["export"]["hvc"]["value"]["total"] = 1000000
        self.expected_response["wins"]["export"]["hvc"]["number"]["total"] = 10

        self.expected_response["wins"]["export"]["totals"]["value"]["confirmed"] = 500000
        self.expected_response["wins"]["export"]["totals"]["value"]["unconfirmed"] = 500000
        self.expected_response["wins"]["export"]["totals"]["value"]["grand_total"] = 1000000
        self.expected_response["wins"]["export"]["totals"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["export"]["totals"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["export"]["totals"]["number"]["grand_total"] = 10

        self.expected_response["wins"]["non_export"]["value"]["confirmed"] = 11500
        self.expected_response["wins"]["non_export"]["value"]["unconfirmed"] = 11500
        self.expected_response["wins"]["non_export"]["value"]["total"] = 23000
        self.expected_response["wins"]["non_export"]["number"]["confirmed"] = 5
        self.expected_response["wins"]["non_export"]["number"]["unconfirmed"] = 5
        self.expected_response["wins"]["non_export"]["number"]["total"] = 10

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

        self.assertEqual(self._api_response_data["avg_time_to_confirm"], 1.0)

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

        self.assertEqual(self._api_response_data["avg_time_to_confirm"], 2.5)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupCampaignViewsTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering `HVCGroup` Campaigns API endpoint
    """
    url = reverse("mi:hvc_group_campaigns", kwargs={"group_id": 4}) + "?year=2016"

    expected_response = {}

    def setUp(self):
        self._win_factory_function = create_win_factory(self.user, sector_choices=self.TEAM_1_SECTORS)

        self.expected_response = {
            "campaigns": [],
            "name": "Automotive",
            "hvcs": {
                "target": GROUP_4_TARGET,
                "campaigns": CAMPAIGNS
            },
            "avg_time_to_confirm": 0.0
        }

    @freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
    def test_cross_fy_wins_in_group_with_change(self):
        """
        This is to test a in that was created in previous FY and confirmed in current FY
        for a team who's name was changed across FYs.
        """
        from django.core.management import call_command
        call_command('create_missing_hvcs', verbose=False)

        self._win_factory_function(hvc_code="E083", confirm=True,
                             export_value=10000000,
                             win_date=datetime.datetime(2017,3, 25),
                             notify_date=datetime.datetime(2017,3, 25),
                             response_date=datetime.datetime(2017,4, 5))
        group_31_campaign_url = reverse("mi:hvc_group_campaigns", kwargs={"group_id": 31}) + "?year=2017"
        api_response = self._get_api_response(group_31_campaign_url)
        response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
        hvc_data = next((item for item in response_decoded["campaigns"] if item["campaign_id"] == "E083"), None)
        self.assertIsNotNone(hvc_data)
        total = hvc_data["totals"]["hvc"]["value"]["confirmed"]
        self.assertEqual(10000000, total)

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
            hvc = HVC.get_by_charcode(hvc_code)

            campaigns.append({
                "campaign": hvc.campaign,
                "campaign_id": hvc.campaign_id,
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

        self.assertResponse()

    def test_sector_team_campaigns_1_wins_for_all_hvcs_unconfirmed(self):
        """ Campaigns api for team 1, with wins for all HVCs"""
        campaigns = []
        for hvc_code in GROUP_4_HVCS:
            WinFactory(user=self.user, hvc=hvc_code)
            hvc = HVC.get_by_charcode(hvc_code)

            campaigns.append({
                "campaign": hvc.campaign,
                "campaign_id": hvc.campaign_id,
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

        self.assertResponse()


def make_month_data(month, confirmed=None, unconfirmed=None):
    if not confirmed:
        confirmed = []
    if not unconfirmed:
        unconfirmed = []

    number_of_unconfirmed_wins = len(unconfirmed)
    number_of_confirmed_wins = len(confirmed)
    number_of_wins = number_of_confirmed_wins + number_of_unconfirmed_wins
    return \
        { 'totals':
            {'non_export':
                {'number': {
                    'total': number_of_wins,
                    'unconfirmed': number_of_unconfirmed_wins,
                    'confirmed': number_of_confirmed_wins
                },
                    'value': {
                        'total': sum([x.total_expected_non_export_value for x in  confirmed + unconfirmed]),
                        'unconfirmed': sum([x.total_expected_non_export_value for x in unconfirmed]),
                        'confirmed': sum([x.total_expected_non_export_value for x in confirmed])
                    }
                },
                'export': {
                    'totals': {
                        'number': {
                            'grand_total': number_of_wins,
                            'unconfirmed': number_of_unconfirmed_wins,
                            'confirmed': number_of_confirmed_wins
                        }, 'value': {
                            'grand_total': sum([x.total_expected_export_value for x in  confirmed + unconfirmed]),
                            'unconfirmed': sum([x.total_expected_export_value for x in unconfirmed]),
                            'confirmed': sum([x.total_expected_export_value for x in confirmed])
                        }
                    },
                    'hvc': {
                        'number': {
                            'total': number_of_wins,
                            'unconfirmed': number_of_unconfirmed_wins,
                            'confirmed': number_of_confirmed_wins
                        },
                        'value': {
                            'total': sum([x.total_expected_export_value for x in confirmed + unconfirmed if x.hvc]),
                            'unconfirmed': sum([x.total_expected_export_value for x in unconfirmed if x.hvc]),
                            'confirmed': sum([x.total_expected_export_value for x in confirmed if x.hvc]),
                        }
                    }
                }
            },
            'date': '2016-{:02d}'.format(month)
        }

@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class HVCGroupMonthsView(MiApiViewsBaseTestCase):
    """
    Tests covering `HVCGroup` Months API endpoint
    """
    url = reverse("mi:hvc_group_months", kwargs={"group_id": 4}) + "?year=2016"

    def setUp(self):

        self.start_month = self.fin_start_date.date().month
        self.end_month = self.frozen_date.date().month

        month_data = [
            make_month_data(x) for x in range(self.start_month, self.end_month + 1)
        ]

        self.expected_response = \
            {
                'name': 'Automotive',
                'months': month_data,
                'avg_time_to_confirm': 0.0,
                'hvcs': {
                    'target': GROUP_4_TARGET,
                    'campaigns': CAMPAIGNS
                },
            }

    def test_month_grouping_with_no_wins(self):
        self.assertResponse()


    def test_month_grouping_with_1_win_unconfirmed(self):
        win1 = WinFactory(
            user=self.user,
            hvc=FuzzyChoice(GROUP_4_HVCS),
            sector=FuzzyChoice(TEAM_SECTORS),
            date=datetime.datetime(2016, 4, 25)
        )
        self.expected_response['months'] = \
            [make_month_data(x, unconfirmed=[win1])
                for x in range(self.start_month, self.end_month + 1)]
        self.assertResponse()

    def test_month_grouping_with_2_uncon_wins_first_month(self):
        win1 = WinFactory(
            user=self.user,
            hvc=FuzzyChoice(GROUP_4_HVCS),
            sector=FuzzyChoice(TEAM_SECTORS),
            date=datetime.datetime(2016, 4, 25)
        )

        month1 = [make_month_data(self.start_month, unconfirmed=[win1])]

        win2 = WinFactory(
            user=self.user,
            hvc=FuzzyChoice(GROUP_4_HVCS),
            sector=FuzzyChoice(TEAM_SECTORS),
            date=datetime.datetime(2016, 5, 25)
        )

        rest_months = [make_month_data(x, unconfirmed=[win1, win2])
                       for x in range(self.start_month + 1, self.end_month + 1)]

        self.expected_response['months'] = month1 + rest_months
        self.assertResponse()


    def test_month_grouping_with_1_win_confirmed(self):
        win1 = WinFactory(
            user=self.user,
            hvc=FuzzyChoice(GROUP_4_HVCS),
            sector=FuzzyChoice(TEAM_SECTORS),
            date=datetime.datetime(2016, 4, 25)
        )
        notification1 = NotificationFactory(win=win1)
        notification1.created = datetime.datetime(2016, 4, 25)
        notification1.save()
        response1 = CustomerResponseFactory(win=win1, agree_with_win=True)
        notification1.created = datetime.datetime(2016, 4, 25)
        response1.save()

        self.expected_response['avg_time_to_confirm'] = 190
        self.expected_response['months'] = \
            [make_month_data(x, confirmed=[win1])
             for x in range(self.start_month, self.end_month + 1)]
        self.assertResponse()

    def test_bad_group_id_is_400_bad_request(self):
        bad_url = reverse("mi:hvc_group_months", kwargs={"group_id": 99}) + "?year=2016"
        self._get_api_response(bad_url, status_code=400)

    def test_no_group_id_is_not_found(self):
        with self.assertRaises(NoReverseMatch):
            reverse("mi:hvc_group_months") + "?year=2016"


class HVCGroupBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):
    export_value = 100000
    win_date_2017 = datetime.datetime(2017, 5, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())
    fy_2016_last_date = datetime.datetime(2017, 3, 31, tzinfo=get_current_timezone())
    frozen_date_17 = datetime.datetime(2017, 5, 31, tzinfo=get_current_timezone())

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)


@freeze_time(HVCGroupBaseViewTestCase.frozen_date_17)
class HVCGroupWinTableTestCase(HVCGroupBaseViewTestCase, GenericWinTableTestMixin):

    fin_years = [2016, 2017]

    TEST_COUNTRY_CODE = 'HU'
    TEST_CAMPAIGN_ID = "E017"
    win_table_url = reverse('mi:hvc_group_win_table', kwargs={"group_id": 4})
    win_table_url_invalid = reverse('mi:hvc_group_win_table', kwargs={"group_id": 100})

    # disable non_hvc tests
    test_win_table_2017_confirmed_non_hvc = None
    test_win_table_2017_unconfirmed_non_hvc = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.win_table_url
        self.expected_response = {
            "hvc_group": {
                "id": "4",
                "name": "Automotive",
            },
            "wins": {
                "hvc": []
            }
        }

    def test_2017_win_table_in_2016_404(self):
        self.view_base_url = self.win_table_url_invalid
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_win_table_in_2017_404(self):
        self.view_base_url = self.win_table_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_win_table_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "hvc_group": {
                "id": "4",
                "name": "Automotive",
            },
            "wins": {
                "hvc": []
            }
        }
        self.assertResponse()

    def test_win_table_json_2017_no_wins(self):
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "hvc_group": {
                "id": "4",
                "name": "Automotive",
            },
            "wins": {
                "hvc": []
            }

        }
        self.assertResponse()

    def test_win_table_2017_one_confirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2017,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], "E049")
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_confirmed")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertTrue(win_item["credit"])

    def test_win_table_2017_one_unconfirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], "E049")
        self.assertIsNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "email_not_sent")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_unconfirmed_hvc_win_with_multiple_customer_notifications(self):
        win = self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )

        # add couple of customer notifications
        notify_date = self.win_date_2017 + datetime.timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        notify_date = self.win_date_2017 + datetime.timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)

    def test_win_table_2017_one_unconfirmed_hvc_win_with_multiple_mixed_notifications(self):
        win = self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )

        # add a customer notification
        notify_date = self.win_date_2017 + datetime.timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        # add an officer notification
        notify_date = self.win_date_2017 + datetime.timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_OFFICER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)

    def test_win_table_2017_one_confirmed_rejected_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2017,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], "E049")
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_rejected")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2017(self):
        self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], "E049")
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_rejected")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2017_with_no2017_target(self):
        self._create_hvc_win(
            hvc_code='E001',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 0)

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2016_no_result(self):
        self._create_hvc_win(
            hvc_code='E049',
            win_date=self.win_date_2016,
            response_date=self.win_date_2016,
            confirm=True,
            agree_with_win=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "wins": {
                "hvc": []
            },
            "hvc_group": {
                    "id": "4",
                    "name": "Automotive"
            }
        }
        self.assertResponse()

    def test_win_table_2017_confirmed_non_hvc_empty_result(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "wins": {
                "hvc": []
            },
            "hvc_group": {
                    "id": "4",
                    "name": "Automotive"
            }
        }
        self.assertResponse()

    def test_win_table_2017_unconfirmed_non_hvc_empty_result(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country='HU'
        )
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "wins": {
                "hvc": []
            },
            "hvc_group": {
                    "id": "4",
                    "name": "Automotive"
            }
        }
        self.assertResponse()
