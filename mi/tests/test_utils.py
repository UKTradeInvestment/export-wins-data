import json
from datetime import datetime

from django.test import TestCase

from freezegun import freeze_time

from mi.utils import (
    get_financial_start_date,
    get_financial_end_date,
    month_iterator,
)


class UtilTests(TestCase):
    frozen_date = "2016-11-01"

    @freeze_time(frozen_date)
    def test_today(self):
        assert datetime.now() == datetime.strptime(self.frozen_date, '%Y-%m-%d')

    @freeze_time("2012-05-01")
    def test_financial_year_start_date(self):
        self.assertEqual(get_financial_start_date(), datetime(2012, 4, 1))

    @freeze_time("2012-05-01")
    def test_financial_year_end_date(self):
        self.assertEqual(get_financial_end_date(), datetime(2013, 3, 31))

    @freeze_time("2012-05-01")
    def test_month_iterator_with_current_date_as_end_date(self):
        months_in_fake_year = [(2012, 4), (2012, 5)]
        self.assertEqual(list(month_iterator(get_financial_start_date())), months_in_fake_year)

    @freeze_time("2012-05-01")
    def test_month_iterator(self):
        months_in_fake_year = [(2012, 4), (2012, 5), (2012, 6), (2012, 7), (2012, 8), (2012, 9),
                               (2012, 10), (2012, 11), (2012, 12), (2013, 1), (2013, 2), (2013, 3)]
        self.assertEqual(list(month_iterator(get_financial_start_date(), get_financial_end_date())),
                         months_in_fake_year)

    def test_compare_json(self):
        without_fy = [
            {
                "hvc_performance": {
                    "red": 0,
                    "amber": 0,
                    "zero": 1,
                    "green": 3
                },
                "name": "Advanced Manufacturing",
                "id": 9,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 0,
                            "zero": 0,
                            "green": 1,
                            "amber": 0
                        },
                        "name": "Advanced Manufacturing",
                        "id": 1,
                        "values": {
                            "hvc": {
                                "target": 100000000,
                                "target_percent": {
                                    "confirmed": 60.0,
                                    "unconfirmed": 0
                                },
                                "current": {
                                    "confirmed": 60020000,
                                    "unconfirmed": 0
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 0,
                            "amber": 0,
                            "zero": 1,
                            "green": 2
                        },
                        "name": "Advanced Manufacturing - Marine",
                        "id": 2,
                        "values": {
                            "hvc": {
                                "target": 80000000,
                                "target_percent": {
                                    "confirmed": 232.0,
                                    "unconfirmed": 42.0
                                },
                                "current": {
                                    "confirmed": 185363000,
                                    "unconfirmed": 33650000
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 273481881,
                            "unconfirmed": 16447422
                        },
                        "total_win_percent": {
                            "confirmed": 53,
                            "unconfirmed": 33
                        }
                    },
                    "totals": {
                        "confirmed": 518864881,
                        "unconfirmed": 50097422
                    },
                    "hvc": {
                        "target": 180000000,
                        "target_percent": {
                            "confirmed": 136.0,
                            "unconfirmed": 19.0
                        },
                        "current": {
                            "confirmed": 245383000,
                            "unconfirmed": 33650000
                        },
                        "total_win_percent": {
                            "confirmed": 47,
                            "unconfirmed": 67
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 0,
                    "amber": 1,
                    "zero": 11,
                    "green": 3
                },
                "name": "Aerospace",
                "id": 5,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 0,
                            "amber": 1,
                            "zero": 11,
                            "green": 3
                        },
                        "name": "Aerospace",
                        "id": 3,
                        "values": {
                            "hvc": {
                                "target": 338500000,
                                "target_percent": {
                                    "confirmed": 2025.0,
                                    "unconfirmed": 211.0
                                },
                                "current": {
                                    "confirmed": 6855370742,
                                    "unconfirmed": 715000000
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 1321012391,
                            "unconfirmed": 607119
                        },
                        "total_win_percent": {
                            "confirmed": 16,
                            "unconfirmed": 0
                        }
                    },
                    "totals": {
                        "confirmed": 8176383133,
                        "unconfirmed": 715607119
                    },
                    "hvc": {
                        "target": 338500000,
                        "target_percent": {
                            "confirmed": 2025.0,
                            "unconfirmed": 211.0
                        },
                        "current": {
                            "confirmed": 6855370742,
                            "unconfirmed": 715000000
                        },
                        "total_win_percent": {
                            "confirmed": 84,
                            "unconfirmed": 100
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 1,
                    "amber": 2,
                    "zero": 0,
                    "green": 4
                },
                "name": "Automotive",
                "id": 11,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 1,
                            "amber": 2,
                            "zero": 0,
                            "green": 4
                        },
                        "name": "Automotive",
                        "id": 4,
                        "values": {
                            "hvc": {
                                "target": 239000000,
                                "target_percent": {
                                    "confirmed": 2445.0,
                                    "unconfirmed": 1.0
                                },
                                "current": {
                                    "confirmed": 5843331656,
                                    "unconfirmed": 2749409
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 924780719,
                            "unconfirmed": 4781190
                        },
                        "total_win_percent": {
                            "confirmed": 14,
                            "unconfirmed": 63
                        }
                    },
                    "totals": {
                        "confirmed": 6768112375,
                        "unconfirmed": 7530599
                    },
                    "hvc": {
                        "target": 239000000,
                        "target_percent": {
                            "confirmed": 2445.0,
                            "unconfirmed": 1.0
                        },
                        "current": {
                            "confirmed": 5843331656,
                            "unconfirmed": 2749409
                        },
                        "total_win_percent": {
                            "confirmed": 86,
                            "unconfirmed": 37
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 3,
                    "amber": 1,
                    "zero": 0,
                    "green": 4
                },
                "name": "Bio-economy",
                "id": 13,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 0,
                            "zero": 0,
                            "green": 3,
                            "amber": 0
                        },
                        "name": "Bio-economy - Agritech",
                        "id": 5,
                        "values": {
                            "hvc": {
                                "target": 30500000,
                                "target_percent": {
                                    "confirmed": 197.0,
                                    "unconfirmed": 0
                                },
                                "current": {
                                    "confirmed": 59965000,
                                    "unconfirmed": 0
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 3,
                            "amber": 1,
                            "zero": 0,
                            "green": 1
                        },
                        "name": "Bio-economy - Chemicals",
                        "id": 6,
                        "values": {
                            "hvc": {
                                "target": 55000000,
                                "target_percent": {
                                    "confirmed": 60.0,
                                    "unconfirmed": 0
                                },
                                "current": {
                                    "confirmed": 33218000,
                                    "unconfirmed": 0
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 31992157,
                            "unconfirmed": 8284357
                        },
                        "total_win_percent": {
                            "confirmed": 26,
                            "unconfirmed": 100
                        }
                    },
                    "totals": {
                        "confirmed": 125175157,
                        "unconfirmed": 8284357
                    },
                    "hvc": {
                        "target": 85500000,
                        "target_percent": {
                            "confirmed": 109.0,
                            "unconfirmed": 0
                        },
                        "current": {
                            "confirmed": 93183000,
                            "unconfirmed": 0
                        },
                        "total_win_percent": {
                            "confirmed": 74,
                            "unconfirmed": 0
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 5,
                    "green": 13,
                    "amber": 1,
                    "zero": 1
                },
                "name": "Consumer & Creative",
                "id": 10,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 3,
                            "amber": 0,
                            "zero": 1,
                            "green": 7
                        },
                        "name": "Consumer Goods & Retail",
                        "id": 7,
                        "values": {
                            "hvc": {
                                "target": 679310000,
                                "target_percent": {
                                    "confirmed": 128.0,
                                    "unconfirmed": 12.0
                                },
                                "current": {
                                    "confirmed": 870406751,
                                    "unconfirmed": 83994250
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 0,
                            "amber": 1,
                            "zero": 0,
                            "green": 4
                        },
                        "name": "Creative Industries",
                        "id": 8,
                        "values": {
                            "hvc": {
                                "target": 401400000,
                                "target_percent": {
                                    "confirmed": 131.0,
                                    "unconfirmed": 2.0
                                },
                                "current": {
                                    "confirmed": 527365366,
                                    "unconfirmed": 6901565
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 2,
                            "amber": 0,
                            "zero": 0,
                            "green": 2
                        },
                        "name": "Sports Economy",
                        "id": 27,
                        "values": {
                            "hvc": {
                                "target": 161000000,
                                "target_percent": {
                                    "confirmed": 98.0,
                                    "unconfirmed": 3.0
                                },
                                "current": {
                                    "confirmed": 157407900,
                                    "unconfirmed": 4284000
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 476184291,
                            "unconfirmed": 35958978
                        },
                        "total_win_percent": {
                            "confirmed": 23,
                            "unconfirmed": 27
                        }
                    },
                    "totals": {
                        "confirmed": 2031364308,
                        "unconfirmed": 131138793
                    },
                    "hvc": {
                        "target": 1241710000,
                        "target_percent": {
                            "confirmed": 125.0,
                            "unconfirmed": 8.0
                        },
                        "current": {
                            "confirmed": 1555180017,
                            "unconfirmed": 95179815
                        },
                        "total_win_percent": {
                            "confirmed": 77,
                            "unconfirmed": 73
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 15,
                    "green": 11,
                    "amber": 4,
                    "zero": 4
                },
                "name": "Defence & Security",
                "id": 14,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 14,
                            "green": 11,
                            "amber": 4,
                            "zero": 4
                        },
                        "name": "Defence",
                        "id": 9,
                        "values": {
                            "hvc": {
                                "target": 3731200000,
                                "target_percent": {
                                    "confirmed": 79.0,
                                    "unconfirmed": 80.0
                                },
                                "current": {
                                    "confirmed": 2933539307,
                                    "unconfirmed": 2975051952
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 1,
                            "zero": 0,
                            "green": 0,
                            "amber": 0
                        },
                        "name": "Strategic Campaigns",
                        "id": 28,
                        "values": {
                            "hvc": {
                                "target": 20000000,
                                "target_percent": {
                                    "confirmed": 0,
                                    "unconfirmed": 0
                                },
                                "current": {
                                    "confirmed": 0,
                                    "unconfirmed": 0
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 279638241,
                            "unconfirmed": 50788059
                        },
                        "total_win_percent": {
                            "confirmed": 9,
                            "unconfirmed": 2
                        }
                    },
                    "totals": {
                        "confirmed": 3213177548,
                        "unconfirmed": 3025840011
                    },
                    "hvc": {
                        "target": 3751200000,
                        "target_percent": {
                            "confirmed": 78.0,
                            "unconfirmed": 79.0
                        },
                        "current": {
                            "confirmed": 2933539307,
                            "unconfirmed": 2975051952
                        },
                        "total_win_percent": {
                            "confirmed": 91,
                            "unconfirmed": 98
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 1,
                    "amber": 0,
                    "zero": 0,
                    "green": 5
                },
                "name": "Education",
                "id": 2,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 1,
                            "amber": 0,
                            "zero": 0,
                            "green": 5
                        },
                        "name": "Education",
                        "id": 11,
                        "values": {
                            "hvc": {
                                "target": 492360000,
                                "target_percent": {
                                    "confirmed": 77.0,
                                    "unconfirmed": 14.0
                                },
                                "current": {
                                    "confirmed": 381378613,
                                    "unconfirmed": 69192253
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 31866865,
                            "unconfirmed": 17038725
                        },
                        "total_win_percent": {
                            "confirmed": 8,
                            "unconfirmed": 20
                        }
                    },
                    "totals": {
                        "confirmed": 413245478,
                        "unconfirmed": 86230978
                    },
                    "hvc": {
                        "target": 492360000,
                        "target_percent": {
                            "confirmed": 77.0,
                            "unconfirmed": 14.0
                        },
                        "current": {
                            "confirmed": 381378613,
                            "unconfirmed": 69192253
                        },
                        "total_win_percent": {
                            "confirmed": 92,
                            "unconfirmed": 80
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 10,
                    "green": 11,
                    "amber": 1,
                    "zero": 2
                },
                "name": "Energy",
                "id": 7,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 3,
                            "amber": 0,
                            "zero": 0,
                            "green": 4
                        },
                        "name": "Energy - Nuclear",
                        "id": 12,
                        "values": {
                            "hvc": {
                                "target": 282800000,
                                "target_percent": {
                                    "confirmed": 62.0,
                                    "unconfirmed": 1.0
                                },
                                "current": {
                                    "confirmed": 175511399,
                                    "unconfirmed": 2160000
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 0,
                            "zero": 0,
                            "green": 1,
                            "amber": 0
                        },
                        "name": "Energy - Offshore Wind",
                        "id": 13,
                        "values": {
                            "hvc": {
                                "target": 65000000,
                                "target_percent": {
                                    "confirmed": 102.0,
                                    "unconfirmed": 2.0
                                },
                                "current": {
                                    "confirmed": 66503743,
                                    "unconfirmed": 1500000
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 6,
                            "green": 4,
                            "amber": 1,
                            "zero": 1
                        },
                        "name": "Energy - Oil & Gas",
                        "id": 14,
                        "values": {
                            "hvc": {
                                "target": 4731055000,
                                "target_percent": {
                                    "confirmed": 69.0,
                                    "unconfirmed": 4.0
                                },
                                "current": {
                                    "confirmed": 3257756556,
                                    "unconfirmed": 188760560
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 1,
                            "amber": 0,
                            "zero": 1,
                            "green": 2
                        },
                        "name": "Energy - Renewables",
                        "id": 15,
                        "values": {
                            "hvc": {
                                "target": 71500000,
                                "target_percent": {
                                    "confirmed": 55.0,
                                    "unconfirmed": 35.0
                                },
                                "current": {
                                    "confirmed": 39121564,
                                    "unconfirmed": 25130172
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 1097949618,
                            "unconfirmed": 2243353054
                        },
                        "total_win_percent": {
                            "confirmed": 24,
                            "unconfirmed": 91
                        }
                    },
                    "totals": {
                        "confirmed": 4636842880,
                        "unconfirmed": 2460903786
                    },
                    "hvc": {
                        "target": 5150355000,
                        "target_percent": {
                            "confirmed": 69.0,
                            "unconfirmed": 4.0
                        },
                        "current": {
                            "confirmed": 3538893262,
                            "unconfirmed": 217550732
                        },
                        "total_win_percent": {
                            "confirmed": 76,
                            "unconfirmed": 9
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 3,
                    "amber": 2,
                    "zero": 0,
                    "green": 5
                },
                "name": "Financial & Professional Services",
                "id": 1,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 3,
                            "amber": 1,
                            "zero": 0,
                            "green": 5
                        },
                        "name": "Financial Services",
                        "id": 16,
                        "values": {
                            "hvc": {
                                "target": 1492140000,
                                "target_percent": {
                                    "confirmed": 154.0,
                                    "unconfirmed": 15.0
                                },
                                "current": {
                                    "confirmed": 2294307056,
                                    "unconfirmed": 230077500
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 0,
                            "zero": 0,
                            "green": 0,
                            "amber": 1
                        },
                        "name": "Professional Services",
                        "id": 26,
                        "values": {
                            "hvc": {
                                "target": 125000000,
                                "target_percent": {
                                    "confirmed": 41.0,
                                    "unconfirmed": 0
                                },
                                "current": {
                                    "confirmed": 51655250,
                                    "unconfirmed": 0
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 1604525536,
                            "unconfirmed": 37942694
                        },
                        "total_win_percent": {
                            "confirmed": 41,
                            "unconfirmed": 14
                        }
                    },
                    "totals": {
                        "confirmed": 3950487842,
                        "unconfirmed": 268020194
                    },
                    "hvc": {
                        "target": 1617140000,
                        "target_percent": {
                            "confirmed": 145.0,
                            "unconfirmed": 14.0
                        },
                        "current": {
                            "confirmed": 2345962306,
                            "unconfirmed": 230077500
                        },
                        "total_win_percent": {
                            "confirmed": 59,
                            "unconfirmed": 86
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 4,
                    "amber": 0,
                    "zero": 0,
                    "green": 5
                },
                "name": "Food & Drink",
                "id": 4,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 4,
                            "amber": 0,
                            "zero": 0,
                            "green": 5
                        },
                        "name": "Food & Drink",
                        "id": 17,
                        "values": {
                            "hvc": {
                                "target": 277800000,
                                "target_percent": {
                                    "confirmed": 81.0,
                                    "unconfirmed": 9.0
                                },
                                "current": {
                                    "confirmed": 224408809,
                                    "unconfirmed": 24541652
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 282493109,
                            "unconfirmed": 125827509
                        },
                        "total_win_percent": {
                            "confirmed": 56,
                            "unconfirmed": 84
                        }
                    },
                    "totals": {
                        "confirmed": 506901918,
                        "unconfirmed": 150369161
                    },
                    "hvc": {
                        "target": 277800000,
                        "target_percent": {
                            "confirmed": 81.0,
                            "unconfirmed": 9.0
                        },
                        "current": {
                            "confirmed": 224408809,
                            "unconfirmed": 24541652
                        },
                        "total_win_percent": {
                            "confirmed": 44,
                            "unconfirmed": 16
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 2,
                    "amber": 2,
                    "zero": 0,
                    "green": 3
                },
                "name": "Healthcare",
                "id": 12,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 2,
                            "amber": 2,
                            "zero": 0,
                            "green": 3
                        },
                        "name": "Healthcare",
                        "id": 18,
                        "values": {
                            "hvc": {
                                "target": 1404800000,
                                "target_percent": {
                                    "confirmed": 36.0,
                                    "unconfirmed": 2.0
                                },
                                "current": {
                                    "confirmed": 509896433,
                                    "unconfirmed": 27291555
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 164072208,
                            "unconfirmed": 34186166
                        },
                        "total_win_percent": {
                            "confirmed": 24,
                            "unconfirmed": 56
                        }
                    },
                    "totals": {
                        "confirmed": 673968641,
                        "unconfirmed": 61477721
                    },
                    "hvc": {
                        "target": 1404800000,
                        "target_percent": {
                            "confirmed": 36.0,
                            "unconfirmed": 2.0
                        },
                        "current": {
                            "confirmed": 509896433,
                            "unconfirmed": 27291555
                        },
                        "total_win_percent": {
                            "confirmed": 76,
                            "unconfirmed": 44
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 17,
                    "amber": 4,
                    "zero": 0,
                    "green": 14
                },
                "name": "Infrastructure",
                "id": 6,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 2,
                            "amber": 0,
                            "zero": 0,
                            "green": 2
                        },
                        "name": "Infrastructure - Aid Funded Business",
                        "id": 19,
                        "values": {
                            "hvc": {
                                "target": 393200000,
                                "target_percent": {
                                    "confirmed": 24.0,
                                    "unconfirmed": 1.0
                                },
                                "current": {
                                    "confirmed": 93184410,
                                    "unconfirmed": 2694035
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 3,
                            "amber": 1,
                            "zero": 0,
                            "green": 2
                        },
                        "name": "Infrastructure - Airports",
                        "id": 20,
                        "values": {
                            "hvc": {
                                "target": 1078804750,
                                "target_percent": {
                                    "confirmed": 23.0,
                                    "unconfirmed": 3.0
                                },
                                "current": {
                                    "confirmed": 250855302,
                                    "unconfirmed": 31770000
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 2,
                            "amber": 2,
                            "zero": 0,
                            "green": 3
                        },
                        "name": "Infrastructure - Construction",
                        "id": 21,
                        "values": {
                            "hvc": {
                                "target": 558890000,
                                "target_percent": {
                                    "confirmed": 54.0,
                                    "unconfirmed": 17.0
                                },
                                "current": {
                                    "confirmed": 299196685,
                                    "unconfirmed": 92434748
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 3,
                            "amber": 0,
                            "zero": 0,
                            "green": 2
                        },
                        "name": "Infrastructure - Mining",
                        "id": 22,
                        "values": {
                            "hvc": {
                                "target": 815500000,
                                "target_percent": {
                                    "confirmed": 34.0,
                                    "unconfirmed": 9.0
                                },
                                "current": {
                                    "confirmed": 275629116,
                                    "unconfirmed": 72389106
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 5,
                            "amber": 0,
                            "zero": 0,
                            "green": 3
                        },
                        "name": "Infrastructure - Rail",
                        "id": 23,
                        "values": {
                            "hvc": {
                                "target": 1460500000,
                                "target_percent": {
                                    "confirmed": 22.0,
                                    "unconfirmed": 8.0
                                },
                                "current": {
                                    "confirmed": 319070500,
                                    "unconfirmed": 115728013
                                }
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "red": 2,
                            "amber": 1,
                            "zero": 0,
                            "green": 2
                        },
                        "name": "Infrastructure - Water",
                        "id": 24,
                        "values": {
                            "hvc": {
                                "target": 1044000000,
                                "target_percent": {
                                    "confirmed": 12.0,
                                    "unconfirmed": 0
                                },
                                "current": {
                                    "confirmed": 129777500,
                                    "unconfirmed": 227500
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 333737607,
                            "unconfirmed": 25886521
                        },
                        "total_win_percent": {
                            "confirmed": 20,
                            "unconfirmed": 8
                        }
                    },
                    "totals": {
                        "confirmed": 1701451120,
                        "unconfirmed": 341129923
                    },
                    "hvc": {
                        "target": 5350894750,
                        "target_percent": {
                            "confirmed": 26.0,
                            "unconfirmed": 6.0
                        },
                        "current": {
                            "confirmed": 1367713513,
                            "unconfirmed": 315243402
                        },
                        "total_win_percent": {
                            "confirmed": 80,
                            "unconfirmed": 92
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 5,
                    "amber": 0,
                    "zero": 0,
                    "green": 3
                },
                "name": "Life Sciences",
                "id": 8,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 5,
                            "amber": 0,
                            "zero": 0,
                            "green": 3
                        },
                        "name": "Life Sciences",
                        "id": 25,
                        "values": {
                            "hvc": {
                                "target": 398130000,
                                "target_percent": {
                                    "confirmed": 55.0,
                                    "unconfirmed": 5.0
                                },
                                "current": {
                                    "confirmed": 219438796,
                                    "unconfirmed": 21732500
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 1485204113,
                            "unconfirmed": 12198836
                        },
                        "total_win_percent": {
                            "confirmed": 87,
                            "unconfirmed": 36
                        }
                    },
                    "totals": {
                        "confirmed": 1704642909,
                        "unconfirmed": 33931336
                    },
                    "hvc": {
                        "target": 398130000,
                        "target_percent": {
                            "confirmed": 55.0,
                            "unconfirmed": 5.0
                        },
                        "current": {
                            "confirmed": 219438796,
                            "unconfirmed": 21732500
                        },
                        "total_win_percent": {
                            "confirmed": 13,
                            "unconfirmed": 64
                        }
                    }
                }
            },
            {
                "hvc_performance": {
                    "red": 1,
                    "amber": 2,
                    "zero": 0,
                    "green": 9
                },
                "name": "Technology",
                "id": 3,
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "red": 1,
                            "amber": 2,
                            "zero": 0,
                            "green": 9
                        },
                        "name": "Digital Economy",
                        "id": 10,
                        "values": {
                            "hvc": {
                                "target": 421900000,
                                "target_percent": {
                                    "confirmed": 140.0,
                                    "unconfirmed": 2.0
                                },
                                "current": {
                                    "confirmed": 590347039,
                                    "unconfirmed": 6386245
                                }
                            }
                        }
                    }
                ],
                "values": {
                    "non_hvc": {
                        "current": {
                            "confirmed": 644173677,
                            "unconfirmed": 7270264
                        },
                        "total_win_percent": {
                            "confirmed": 52,
                            "unconfirmed": 53
                        }
                    },
                    "totals": {
                        "confirmed": 1234520716,
                        "unconfirmed": 13656509
                    },
                    "hvc": {
                        "target": 421900000,
                        "target_percent": {
                            "confirmed": 140.0,
                            "unconfirmed": 2.0
                        },
                        "current": {
                            "confirmed": 590347039,
                            "unconfirmed": 6386245
                        },
                        "total_win_percent": {
                            "confirmed": 48,
                            "unconfirmed": 47
                        }
                    }
                }
            }
        ]
        with_fy = [
            {
                "hvc_performance": {
                    "green": 3,
                    "amber": 0,
                    "red": 0,
                    "zero": 1
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "amber": 0,
                            "red": 0,
                            "zero": 0,
                            "green": 1
                        },
                        "id": 1,
                        "name": "Advanced Manufacturing",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 0,
                                    "confirmed": 60.0
                                },
                                "current": {
                                    "unconfirmed": 0,
                                    "confirmed": 60020000
                                },
                                "target": 100000000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 0,
                            "red": 0,
                            "zero": 1
                        },
                        "id": 2,
                        "name": "Advanced Manufacturing - Marine",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 42.0,
                                    "confirmed": 232.0
                                },
                                "current": {
                                    "unconfirmed": 33650000,
                                    "confirmed": 185363000
                                },
                                "target": 80000000
                            }
                        }
                    }
                ],
                "id": 9,
                "name": "Advanced Manufacturing",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 19.0,
                            "confirmed": 136.0
                        },
                        "current": {
                            "unconfirmed": 33650000,
                            "confirmed": 245383000
                        },
                        "total_win_percent": {
                            "unconfirmed": 67,
                            "confirmed": 47
                        },
                        "target": 180000000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 33,
                            "confirmed": 53
                        },
                        "current": {
                            "unconfirmed": 16447422,
                            "confirmed": 273481881
                        }
                    },
                    "totals": {
                        "unconfirmed": 50097422,
                        "confirmed": 518864881
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 3,
                    "amber": 1,
                    "red": 0,
                    "zero": 11
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 3,
                            "amber": 1,
                            "red": 0,
                            "zero": 11
                        },
                        "id": 3,
                        "name": "Aerospace",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 211.0,
                                    "confirmed": 2025.0
                                },
                                "current": {
                                    "unconfirmed": 715000000,
                                    "confirmed": 6855370742
                                },
                                "target": 338500000
                            }
                        }
                    }
                ],
                "id": 5,
                "name": "Aerospace",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 211.0,
                            "confirmed": 2025.0
                        },
                        "current": {
                            "unconfirmed": 715000000,
                            "confirmed": 6855370742
                        },
                        "total_win_percent": {
                            "unconfirmed": 100,
                            "confirmed": 84
                        },
                        "target": 338500000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 0,
                            "confirmed": 16
                        },
                        "current": {
                            "unconfirmed": 607119,
                            "confirmed": 1321012391
                        }
                    },
                    "totals": {
                        "unconfirmed": 715607119,
                        "confirmed": 8176383133
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 4,
                    "amber": 2,
                    "red": 1,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 4,
                            "amber": 2,
                            "red": 1,
                            "zero": 0
                        },
                        "id": 4,
                        "name": "Automotive",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 1.0,
                                    "confirmed": 2445.0
                                },
                                "current": {
                                    "unconfirmed": 2749409,
                                    "confirmed": 5843331656
                                },
                                "target": 239000000
                            }
                        }
                    }
                ],
                "id": 11,
                "name": "Automotive",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 1.0,
                            "confirmed": 2445.0
                        },
                        "current": {
                            "unconfirmed": 2749409,
                            "confirmed": 5843331656
                        },
                        "total_win_percent": {
                            "unconfirmed": 37,
                            "confirmed": 86
                        },
                        "target": 239000000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 63,
                            "confirmed": 14
                        },
                        "current": {
                            "unconfirmed": 4781190,
                            "confirmed": 924780719
                        }
                    },
                    "totals": {
                        "unconfirmed": 7530599,
                        "confirmed": 6768112375
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 4,
                    "amber": 1,
                    "red": 3,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "amber": 0,
                            "red": 0,
                            "zero": 0,
                            "green": 3
                        },
                        "id": 5,
                        "name": "Bio-economy - Agritech",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 0,
                                    "confirmed": 197.0
                                },
                                "current": {
                                    "unconfirmed": 0,
                                    "confirmed": 59965000
                                },
                                "target": 30500000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 1,
                            "amber": 1,
                            "red": 3,
                            "zero": 0
                        },
                        "id": 6,
                        "name": "Bio-economy - Chemicals",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 0,
                                    "confirmed": 60.0
                                },
                                "current": {
                                    "unconfirmed": 0,
                                    "confirmed": 33218000
                                },
                                "target": 55000000
                            }
                        }
                    }
                ],
                "id": 13,
                "name": "Bio-economy",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 0,
                            "confirmed": 109.0
                        },
                        "current": {
                            "unconfirmed": 0,
                            "confirmed": 93183000
                        },
                        "total_win_percent": {
                            "unconfirmed": 0,
                            "confirmed": 74
                        },
                        "target": 85500000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 100,
                            "confirmed": 26
                        },
                        "current": {
                            "unconfirmed": 8284357,
                            "confirmed": 31992157
                        }
                    },
                    "totals": {
                        "unconfirmed": 8284357,
                        "confirmed": 125175157
                    }
                }
            },
            {
                "hvc_performance": {
                    "zero": 1,
                    "green": 13,
                    "amber": 1,
                    "red": 5
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 7,
                            "amber": 0,
                            "red": 3,
                            "zero": 1
                        },
                        "id": 7,
                        "name": "Consumer Goods & Retail",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 12.0,
                                    "confirmed": 128.0
                                },
                                "current": {
                                    "unconfirmed": 83994250,
                                    "confirmed": 870406751
                                },
                                "target": 679310000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 4,
                            "amber": 1,
                            "red": 0,
                            "zero": 0
                        },
                        "id": 8,
                        "name": "Creative Industries",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 2.0,
                                    "confirmed": 131.0
                                },
                                "current": {
                                    "unconfirmed": 6901565,
                                    "confirmed": 527365366
                                },
                                "target": 401400000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 0,
                            "red": 2,
                            "zero": 0
                        },
                        "id": 27,
                        "name": "Sports Economy",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 3.0,
                                    "confirmed": 98.0
                                },
                                "current": {
                                    "unconfirmed": 4284000,
                                    "confirmed": 157407900
                                },
                                "target": 161000000
                            }
                        }
                    }
                ],
                "id": 10,
                "name": "Consumer & Creative",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 8.0,
                            "confirmed": 125.0
                        },
                        "current": {
                            "unconfirmed": 95179815,
                            "confirmed": 1555180017
                        },
                        "total_win_percent": {
                            "unconfirmed": 73,
                            "confirmed": 77
                        },
                        "target": 1241710000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 27,
                            "confirmed": 23
                        },
                        "current": {
                            "unconfirmed": 35958978,
                            "confirmed": 476184291
                        }
                    },
                    "totals": {
                        "unconfirmed": 131138793,
                        "confirmed": 2031364308
                    }
                }
            },
            {
                "hvc_performance": {
                    "zero": 4,
                    "green": 11,
                    "amber": 4,
                    "red": 15
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "zero": 4,
                            "green": 11,
                            "amber": 4,
                            "red": 14
                        },
                        "id": 9,
                        "name": "Defence",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 80.0,
                                    "confirmed": 79.0
                                },
                                "current": {
                                    "unconfirmed": 2975051952,
                                    "confirmed": 2933539307
                                },
                                "target": 3731200000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "amber": 0,
                            "red": 1,
                            "zero": 0,
                            "green": 0
                        },
                        "id": 28,
                        "name": "Strategic Campaigns",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 0,
                                    "confirmed": 0
                                },
                                "current": {
                                    "unconfirmed": 0,
                                    "confirmed": 0
                                },
                                "target": 20000000
                            }
                        }
                    }
                ],
                "id": 14,
                "name": "Defence & Security",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 79.0,
                            "confirmed": 78.0
                        },
                        "current": {
                            "unconfirmed": 2975051952,
                            "confirmed": 2933539307
                        },
                        "total_win_percent": {
                            "unconfirmed": 98,
                            "confirmed": 91
                        },
                        "target": 3751200000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 2,
                            "confirmed": 9
                        },
                        "current": {
                            "unconfirmed": 50788059,
                            "confirmed": 279638241
                        }
                    },
                    "totals": {
                        "unconfirmed": 3025840011,
                        "confirmed": 3213177548
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 5,
                    "amber": 0,
                    "red": 1,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 5,
                            "amber": 0,
                            "red": 1,
                            "zero": 0
                        },
                        "id": 11,
                        "name": "Education",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 14.0,
                                    "confirmed": 77.0
                                },
                                "current": {
                                    "unconfirmed": 69192253,
                                    "confirmed": 381378613
                                },
                                "target": 492360000
                            }
                        }
                    }
                ],
                "id": 2,
                "name": "Education",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 14.0,
                            "confirmed": 77.0
                        },
                        "current": {
                            "unconfirmed": 69192253,
                            "confirmed": 381378613
                        },
                        "total_win_percent": {
                            "unconfirmed": 80,
                            "confirmed": 92
                        },
                        "target": 492360000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 20,
                            "confirmed": 8
                        },
                        "current": {
                            "unconfirmed": 17038725,
                            "confirmed": 31866865
                        }
                    },
                    "totals": {
                        "unconfirmed": 86230978,
                        "confirmed": 413245478
                    }
                }
            },
            {
                "hvc_performance": {
                    "zero": 2,
                    "green": 11,
                    "amber": 1,
                    "red": 10
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 4,
                            "amber": 0,
                            "red": 3,
                            "zero": 0
                        },
                        "id": 12,
                        "name": "Energy - Nuclear",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 1.0,
                                    "confirmed": 62.0
                                },
                                "current": {
                                    "unconfirmed": 2160000,
                                    "confirmed": 175511399
                                },
                                "target": 282800000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "amber": 0,
                            "red": 0,
                            "zero": 0,
                            "green": 1
                        },
                        "id": 13,
                        "name": "Energy - Offshore Wind",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 2.0,
                                    "confirmed": 102.0
                                },
                                "current": {
                                    "unconfirmed": 1500000,
                                    "confirmed": 66503743
                                },
                                "target": 65000000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "zero": 1,
                            "green": 4,
                            "amber": 1,
                            "red": 6
                        },
                        "id": 14,
                        "name": "Energy - Oil & Gas",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 4.0,
                                    "confirmed": 69.0
                                },
                                "current": {
                                    "unconfirmed": 188760560,
                                    "confirmed": 3257756556
                                },
                                "target": 4731055000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 0,
                            "red": 1,
                            "zero": 1
                        },
                        "id": 15,
                        "name": "Energy - Renewables",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 35.0,
                                    "confirmed": 55.0
                                },
                                "current": {
                                    "unconfirmed": 25130172,
                                    "confirmed": 39121564
                                },
                                "target": 71500000
                            }
                        }
                    }
                ],
                "id": 7,
                "name": "Energy",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 4.0,
                            "confirmed": 69.0
                        },
                        "current": {
                            "unconfirmed": 217550732,
                            "confirmed": 3538893262
                        },
                        "total_win_percent": {
                            "unconfirmed": 9,
                            "confirmed": 76
                        },
                        "target": 5150355000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 91,
                            "confirmed": 24
                        },
                        "current": {
                            "unconfirmed": 2243353054,
                            "confirmed": 1097949618
                        }
                    },
                    "totals": {
                        "unconfirmed": 2460903786,
                        "confirmed": 4636842880
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 5,
                    "amber": 2,
                    "red": 3,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 5,
                            "amber": 1,
                            "red": 3,
                            "zero": 0
                        },
                        "id": 16,
                        "name": "Financial Services",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 15.0,
                                    "confirmed": 154.0
                                },
                                "current": {
                                    "unconfirmed": 230077500,
                                    "confirmed": 2294307056
                                },
                                "target": 1492140000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "amber": 1,
                            "red": 0,
                            "zero": 0,
                            "green": 0
                        },
                        "id": 26,
                        "name": "Professional Services",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 0,
                                    "confirmed": 41.0
                                },
                                "current": {
                                    "unconfirmed": 0,
                                    "confirmed": 51655250
                                },
                                "target": 125000000
                            }
                        }
                    }
                ],
                "id": 1,
                "name": "Financial & Professional Services",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 14.0,
                            "confirmed": 145.0
                        },
                        "current": {
                            "unconfirmed": 230077500,
                            "confirmed": 2345962306
                        },
                        "total_win_percent": {
                            "unconfirmed": 86,
                            "confirmed": 59
                        },
                        "target": 1617140000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 14,
                            "confirmed": 41
                        },
                        "current": {
                            "unconfirmed": 37942694,
                            "confirmed": 1604525536
                        }
                    },
                    "totals": {
                        "unconfirmed": 268020194,
                        "confirmed": 3950487842
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 5,
                    "amber": 0,
                    "red": 4,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 5,
                            "amber": 0,
                            "red": 4,
                            "zero": 0
                        },
                        "id": 17,
                        "name": "Food & Drink",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 9.0,
                                    "confirmed": 81.0
                                },
                                "current": {
                                    "unconfirmed": 24541652,
                                    "confirmed": 224408809
                                },
                                "target": 277800000
                            }
                        }
                    }
                ],
                "id": 4,
                "name": "Food & Drink",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 9.0,
                            "confirmed": 81.0
                        },
                        "current": {
                            "unconfirmed": 24541652,
                            "confirmed": 224408809
                        },
                        "total_win_percent": {
                            "unconfirmed": 16,
                            "confirmed": 44
                        },
                        "target": 277800000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 84,
                            "confirmed": 56
                        },
                        "current": {
                            "unconfirmed": 125827509,
                            "confirmed": 282493109
                        }
                    },
                    "totals": {
                        "unconfirmed": 150369161,
                        "confirmed": 506901918
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 3,
                    "amber": 2,
                    "red": 2,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 3,
                            "amber": 2,
                            "red": 2,
                            "zero": 0
                        },
                        "id": 18,
                        "name": "Healthcare",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 2.0,
                                    "confirmed": 36.0
                                },
                                "current": {
                                    "unconfirmed": 27291555,
                                    "confirmed": 509896433
                                },
                                "target": 1404800000
                            }
                        }
                    }
                ],
                "id": 12,
                "name": "Healthcare",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 2.0,
                            "confirmed": 36.0
                        },
                        "current": {
                            "unconfirmed": 27291555,
                            "confirmed": 509896433
                        },
                        "total_win_percent": {
                            "unconfirmed": 44,
                            "confirmed": 76
                        },
                        "target": 1404800000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 56,
                            "confirmed": 24
                        },
                        "current": {
                            "unconfirmed": 34186166,
                            "confirmed": 164072208
                        }
                    },
                    "totals": {
                        "unconfirmed": 61477721,
                        "confirmed": 673968641
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 14,
                    "amber": 4,
                    "red": 17,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 0,
                            "red": 2,
                            "zero": 0
                        },
                        "id": 19,
                        "name": "Infrastructure - Aid Funded Business",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 1.0,
                                    "confirmed": 24.0
                                },
                                "current": {
                                    "unconfirmed": 2694035,
                                    "confirmed": 93184410
                                },
                                "target": 393200000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 1,
                            "red": 3,
                            "zero": 0
                        },
                        "id": 20,
                        "name": "Infrastructure - Airports",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 3.0,
                                    "confirmed": 23.0
                                },
                                "current": {
                                    "unconfirmed": 31770000,
                                    "confirmed": 250855302
                                },
                                "target": 1078804750
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 3,
                            "amber": 2,
                            "red": 2,
                            "zero": 0
                        },
                        "id": 21,
                        "name": "Infrastructure - Construction",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 17.0,
                                    "confirmed": 54.0
                                },
                                "current": {
                                    "unconfirmed": 92434748,
                                    "confirmed": 299196685
                                },
                                "target": 558890000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 0,
                            "red": 3,
                            "zero": 0
                        },
                        "id": 22,
                        "name": "Infrastructure - Mining",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 9.0,
                                    "confirmed": 34.0
                                },
                                "current": {
                                    "unconfirmed": 72389106,
                                    "confirmed": 275629116
                                },
                                "target": 815500000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 3,
                            "amber": 0,
                            "red": 5,
                            "zero": 0
                        },
                        "id": 23,
                        "name": "Infrastructure - Rail",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 8.0,
                                    "confirmed": 22.0
                                },
                                "current": {
                                    "unconfirmed": 115728013,
                                    "confirmed": 319070500
                                },
                                "target": 1460500000
                            }
                        }
                    },
                    {
                        "hvc_performance": {
                            "green": 2,
                            "amber": 1,
                            "red": 2,
                            "zero": 0
                        },
                        "id": 24,
                        "name": "Infrastructure - Water",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 0,
                                    "confirmed": 12.0
                                },
                                "current": {
                                    "unconfirmed": 227500,
                                    "confirmed": 129777500
                                },
                                "target": 1044000000
                            }
                        }
                    }
                ],
                "id": 6,
                "name": "Infrastructure",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 6.0,
                            "confirmed": 26.0
                        },
                        "current": {
                            "unconfirmed": 315243402,
                            "confirmed": 1367713513
                        },
                        "total_win_percent": {
                            "unconfirmed": 92,
                            "confirmed": 80
                        },
                        "target": 5350894750
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 8,
                            "confirmed": 20
                        },
                        "current": {
                            "unconfirmed": 25886521,
                            "confirmed": 333737607
                        }
                    },
                    "totals": {
                        "unconfirmed": 341129923,
                        "confirmed": 1701451120
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 3,
                    "amber": 0,
                    "red": 5,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 3,
                            "amber": 0,
                            "red": 5,
                            "zero": 0
                        },
                        "id": 25,
                        "name": "Life Sciences",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 5.0,
                                    "confirmed": 55.0
                                },
                                "current": {
                                    "unconfirmed": 21732500,
                                    "confirmed": 219438796
                                },
                                "target": 398130000
                            }
                        }
                    }
                ],
                "id": 8,
                "name": "Life Sciences",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 5.0,
                            "confirmed": 55.0
                        },
                        "current": {
                            "unconfirmed": 21732500,
                            "confirmed": 219438796
                        },
                        "total_win_percent": {
                            "unconfirmed": 64,
                            "confirmed": 13
                        },
                        "target": 398130000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 36,
                            "confirmed": 87
                        },
                        "current": {
                            "unconfirmed": 12198836,
                            "confirmed": 1485204113
                        }
                    },
                    "totals": {
                        "unconfirmed": 33931336,
                        "confirmed": 1704642909
                    }
                }
            },
            {
                "hvc_performance": {
                    "green": 9,
                    "amber": 2,
                    "red": 1,
                    "zero": 0
                },
                "hvc_groups": [
                    {
                        "hvc_performance": {
                            "green": 9,
                            "amber": 2,
                            "red": 1,
                            "zero": 0
                        },
                        "id": 10,
                        "name": "Digital Economy",
                        "values": {
                            "hvc": {
                                "target_percent": {
                                    "unconfirmed": 2.0,
                                    "confirmed": 140.0
                                },
                                "current": {
                                    "unconfirmed": 6386245,
                                    "confirmed": 590347039
                                },
                                "target": 421900000
                            }
                        }
                    }
                ],
                "id": 3,
                "name": "Technology",
                "values": {
                    "hvc": {
                        "target_percent": {
                            "unconfirmed": 2.0,
                            "confirmed": 140.0
                        },
                        "current": {
                            "unconfirmed": 6386245,
                            "confirmed": 590347039
                        },
                        "total_win_percent": {
                            "unconfirmed": 47,
                            "confirmed": 48
                        },
                        "target": 421900000
                    },
                    "non_hvc": {
                        "total_win_percent": {
                            "unconfirmed": 53,
                            "confirmed": 52
                        },
                        "current": {
                            "unconfirmed": 7270264,
                            "confirmed": 644173677
                        }
                    },
                    "totals": {
                        "unconfirmed": 13656509,
                        "confirmed": 1234520716
                    }
                }
            }
        ]
        self.assertJSONEqual(json.dumps(without_fy), json.dumps(with_fy))
