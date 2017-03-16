import datetime

from django.core.urlresolvers import reverse
from factory.fuzzy import FuzzyChoice
from freezegun import freeze_time

from mi.tests.base_test_case import MiApiViewsBaseTestCase
from mi.utils import sort_campaigns_by
from wins.factories import (
    CustomerResponseFactory,
    NotificationFactory,
    WinFactory,
)
from wins.models import HVC


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamListTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering SectorTeam overview and detail API endpoints
    """

    url = reverse('mi:sector_teams')

    def test_sector_teams_list(self):
        """ test `SectorTeam` list API """

        self.expected_response = sorted([
            {
                "id": 1,
                "name": "Financial & Professional Services",
                "hvc_groups": [
                    {
                        "id": 16,
                        "name": "Financial Services"
                    },
                    {
                        "id": 26,
                        "name": "Professional Services"
                    }
                ]
            },
            {
                "id": 2,
                "name": "Education",
                "hvc_groups": [
                    {
                        "id": 11,
                        "name": "Education"
                    }
                ]
            },
            {
                "id": 3,
                "name": "Technology",
                "hvc_groups": [
                    {
                        "id": 10,
                        "name": "Digital Economy"
                    }
                ]
            },
            {
                "id": 4,
                "name": "Food & Drink",
                "hvc_groups": [
                    {
                        "id": 17,
                        "name": "Food & Drink"
                    }
                ]
            },
            {
                "id": 5,
                "name": "Aerospace",
                "hvc_groups": [
                    {
                        "id": 3,
                        "name": "Aerospace"
                    }
                ]
            },
            {
                "id": 6,
                "name": "Infrastructure",
                "hvc_groups": [
                    {
                        "id": 19,
                        "name": "Infrastructure - Aid Funded Business"
                    },
                    {
                        "id": 20,
                        "name": "Infrastructure - Airports"
                    },
                    {
                        "id": 21,
                        "name": "Infrastructure - Construction"
                    },
                    {
                        "id": 22,
                        "name": "Infrastructure - Mining"
                    },
                    {
                        "id": 23,
                        "name": "Infrastructure - Rail"
                    },
                    {
                        "id": 24,
                        "name": "Infrastructure - Water"
                    }
                ]
            },
            {
                "id": 7,
                "name": "Energy",
                "hvc_groups": [
                    {
                        "id": 12,
                        "name": "Energy - Nuclear"
                    },
                    {
                        "id": 13,
                        "name": "Energy - Offshore Wind"
                    },
                    {
                        "id": 14,
                        "name": "Energy - Oil & Gas"
                    },
                    {
                        "id": 15,
                        "name": "Energy - Renewables"
                    }
                ]
            },
            {
                "id": 8,
                "name": "Life Sciences",
                "hvc_groups": [
                    {
                        "id": 25,
                        "name": "Life Sciences"
                    }
                ]
            },
            {
                "id": 9,
                "name": "Advanced Manufacturing",
                "hvc_groups": [
                    {
                        "id": 1,
                        "name": "Advanced Manufacturing"
                    },
                    {
                        "id": 2,
                        "name": "Advanced Manufacturing - Marine"
                    }
                ]
            },
            {
                "id": 10,
                "name": "Consumer & Creative",
                "hvc_groups": [
                    {
                        "id": 7,
                        "name": "Consumer Goods & Retail"
                    },
                    {
                        "id": 8,
                        "name": "Creative Industries"
                    },
                    {
                        "id": 27,
                        "name": "Sports Economy"
                    }
                ]
            },
            {
                "id": 11,
                "name": "Automotive",
                "hvc_groups": [
                    {
                        "id": 4,
                        "name": "Automotive"
                    }
                ]
            },
            {
                "id": 12,
                "name": "Healthcare",
                "hvc_groups": [
                    {
                        "id": 18,
                        "name": "Healthcare"
                    }
                ]
            },
            {
                "id": 13,
                "name": "Bio-economy",
                "hvc_groups": [
                    {
                        "id": 5,
                        "name": "Bio-economy - Agritech"
                    },
                    {
                        "id": 6,
                        "name": "Bio-economy - Chemicals"
                    }
                ]
            },
            {
                "id": 14,
                "name": "Defence & Security",
                "hvc_groups": [
                    {
                        "id": 9,
                        "name": "Defence"
                    },
                    {
                        "id": 28,
                        "name": "Strategic Campaigns"
                    }
                ]
            }
        ], key=lambda x: (x['name']))
        self.assertResponse()


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamCampaignViewsTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering SectorTeam Campaigns API endpoint
    """
    expected_response = {}

    def setUp(self):
        self.expected_response = {
            "campaigns": [],
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

    def test_sector_team_campaigns_1_wins_for_all_hvcs(self):
        """ Campaigns api for team 1, with wins for all HVCs"""
        campaigns = []
        count = len(self.TEAM_1_HVCS)
        for hvc_code in self.TEAM_1_HVCS:
            # add export value such that we get response in a specific order
            export_value = count * 100000
            percent = (export_value * 100) / self.CAMPAIGN_TARGET
            win = WinFactory(user=self.user, hvc=hvc_code, sector=FuzzyChoice(self.TEAM_1_SECTORS),
                             total_expected_export_value=export_value)
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
                            "confirmed": export_value,
                            "total": export_value
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
                        "confirmed_percent": percent,
                        "status": "red"
                    },
                    "target": self.CAMPAIGN_TARGET
                }
            })

        self.expected_response["campaigns"] = sorted(campaigns, key=sort_campaigns_by, reverse=True)
        self.expected_response["avg_time_to_confirm"] = 4.0

        st_url = reverse('mi:sector_team_campaigns', kwargs={'team_id': 1})
        api_response = self._get_api_response(st_url)
        self.assertJSONEqual(api_response.content.decode("utf-8"), self.expected_response)

    def test_sector_team_campaigns_1_wins_for_all_hvcs_unconfirmed(self):
        """ Campaigns api for team 1, with wins for all HVCs"""
        campaigns = []
        count = len(self.TEAM_1_HVCS)
        for hvc_code in self.TEAM_1_HVCS:
            # add export value such that we get response in a specific order
            export_value = count * 100000
            percent = (export_value * 100) / self.CAMPAIGN_TARGET
            WinFactory(user=self.user, hvc=hvc_code, total_expected_export_value=export_value)
            count -= 1

            campaigns.append({
                "campaign": HVC.objects.get(campaign_id=hvc_code).campaign,
                "campaign_id": hvc_code,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": export_value,
                            "confirmed": 0,
                            "total": export_value
                        },
                        "number": {
                            "unconfirmed": 1,
                            "confirmed": 0,
                            "total": 1
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": percent,
                        "confirmed_percent": 0.0,
                        "status": "red"
                    },
                    "target": self.CAMPAIGN_TARGET
                }
            })

        self.expected_response["campaigns"] = sorted(campaigns, key=lambda c: (
            c['totals']['progress']['confirmed_percent'],
            c['totals']['progress']['unconfirmed_percent'],
            c['totals']['target']), reverse=True)

        st_url = reverse('mi:sector_team_campaigns', kwargs={'team_id': 1})
        api_response = self._get_api_response(st_url)
        self.assertJSONEqual(api_response.content.decode("utf-8"), self.expected_response)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamMonthlyViewsTestCase(MiApiViewsBaseTestCase):
    """
    Tests covering SectorTeam Campaigns API endpoint
    """

    expected_response = {
        "avg_time_to_confirm": 0.0,
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
            "target": 0
        },
        "months": [
            {
                "date": "2016-04",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 2,
                                "unconfirmed": 2
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 200000,
                                "unconfirmed": 200000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 2,
                                "unconfirmed": 2
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 200000,
                                "unconfirmed": 200000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 2,
                            "unconfirmed": 2
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 4600,
                            "unconfirmed": 4600
                        }
                    }
                }
            },
            {
                "date": "2016-05",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 4,
                                "unconfirmed": 4
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 400000,
                                "unconfirmed": 400000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 4,
                                "unconfirmed": 4
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 400000,
                                "unconfirmed": 400000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 4,
                            "unconfirmed": 4
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 9200,
                            "unconfirmed": 9200
                        }
                    }
                }
            },
            {
                "date": "2016-06",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 5,
                                "unconfirmed": 5
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 500000,
                                "unconfirmed": 500000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 5,
                                "unconfirmed": 5
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 500000,
                                "unconfirmed": 500000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 5,
                            "unconfirmed": 5
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 11500,
                            "unconfirmed": 11500
                        }
                    }
                }
            },
            {
                "date": "2016-07",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 6,
                                "unconfirmed": 6
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 600000,
                                "unconfirmed": 600000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 6,
                                "unconfirmed": 6
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 600000,
                                "unconfirmed": 600000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 6,
                            "unconfirmed": 6
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 13800,
                            "unconfirmed": 13800
                        }
                    }
                }
            },
            {
                "date": "2016-08",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 7,
                                "unconfirmed": 7
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 700000,
                                "unconfirmed": 700000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 7,
                                "unconfirmed": 7
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 700000,
                                "unconfirmed": 700000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 7,
                            "unconfirmed": 7
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 16100,
                            "unconfirmed": 16100
                        }
                    }
                }
            },
            {
                "date": "2016-09",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 8,
                                "unconfirmed": 8
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 800000,
                                "unconfirmed": 800000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 8,
                                "unconfirmed": 8
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 800000,
                                "unconfirmed": 800000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 8,
                            "unconfirmed": 8
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 18400,
                            "unconfirmed": 18400
                        }
                    }
                }
            },
            {
                "date": "2016-10",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 9,
                                "unconfirmed": 9
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 900000,
                                "unconfirmed": 900000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 9,
                                "unconfirmed": 9
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 900000,
                                "unconfirmed": 900000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 9,
                            "unconfirmed": 9
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 20700,
                            "unconfirmed": 20700
                        }
                    }
                }
            },
            {
                "date": "2016-11",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 10,
                                "unconfirmed": 10
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 1000000,
                                "unconfirmed": 1000000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 10,
                                "unconfirmed": 10
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 1000000,
                                "unconfirmed": 1000000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 10,
                            "unconfirmed": 10
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 23000,
                            "unconfirmed": 23000
                        }
                    }
                }
            },
            {
                "date": "2016-12",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 11,
                                "unconfirmed": 11
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 1100000,
                                "unconfirmed": 1100000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 11,
                                "unconfirmed": 11
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 1100000,
                                "unconfirmed": 1100000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 11,
                            "unconfirmed": 11
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 25300,
                            "unconfirmed": 25300
                        }
                    }
                }
            },
            {
                "date": "2017-01",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 12,
                                "unconfirmed": 12
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 1200000,
                                "unconfirmed": 1200000
                            }
                        },
                        "non_hvc": {
                            "number": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 0,
                                "total": 0,
                                "unconfirmed": 0
                            }
                        },
                        "totals": {
                            "number": {
                                "confirmed": 0,
                                "grand_total": 12,
                                "unconfirmed": 12
                            },
                            "value": {
                                "confirmed": 0,
                                "grand_total": 1200000,
                                "unconfirmed": 1200000
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 0,
                            "total": 12,
                            "unconfirmed": 12
                        },
                        "value": {
                            "confirmed": 0,
                            "total": 27600,
                            "unconfirmed": 27600
                        }
                    }
                }
            }
        ],
        "name": "Financial & Professional Services"
    }

    def setUp(self):
        self.expected_response['hvcs']['target'] = self.CAMPAIGN_TARGET * len(self.TEAM_1_HVCS)

    def test_sector_team_month_1(self):
        """ Tests covering SectorTeam Campaigns API endpoint """

        for i in range(4, 13):
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, i, 1),
                       sector=FuzzyChoice(self.TEAM_1_SECTORS))

        # Add few random ones
        WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2017, 1, 1),
                   sector=FuzzyChoice(self.TEAM_1_SECTORS))
        WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 4, 1),
                   sector=FuzzyChoice(self.TEAM_1_SECTORS))
        WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, 5, 1),
                   sector=FuzzyChoice(self.TEAM_1_SECTORS))
        st_url = reverse('mi:sector_team_months', kwargs={'team_id': 1})
        api_response = self._get_api_response(st_url)

        self.assertJSONEqual(api_response.content.decode("utf-8"), self.expected_response)

    def test_sector_team_month_1_some_wins_out_of_date(self):
        """ Check that out of date, wins that were added with date that is not within current financial year
        are not accounted for """

        for i in list(range(3, 13)) + [4, 5]:
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2016, i, 1),
                       sector=FuzzyChoice(self.TEAM_1_SECTORS))

        # add few more random financial year wins, both in and out
        for i in [6, 12]:
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2015, i, 1),
                       sector=FuzzyChoice(self.TEAM_1_SECTORS))
        for i in [1, 4, 8]:
            WinFactory(user=self.user, hvc=FuzzyChoice(self.TEAM_1_HVCS), date=datetime.datetime(2017, i, 1),
                       sector=FuzzyChoice(self.TEAM_1_SECTORS))

        st_url = reverse('mi:sector_team_months', kwargs={'team_id': 1})
        api_response = self._get_api_response(st_url)

        self.assertJSONEqual(api_response.content.decode("utf-8"), self.expected_response)
