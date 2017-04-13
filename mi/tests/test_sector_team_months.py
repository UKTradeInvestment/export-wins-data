import datetime
import json

from django.core.urlresolvers import reverse
from freezegun import freeze_time

from mi.models import FinancialYear
from mi.tests.base_test_case import MiApiViewsBaseTestCase
from mi.tests.test_sector_views import SectorTeamBaseTestCase

from mi.utils import (
    month_iterator,
    get_financial_start_date
)


@freeze_time(MiApiViewsBaseTestCase.frozen_date)
class SectorTeamMonthlyViewsTestCase(SectorTeamBaseTestCase):
    """
    Tests covering SectorTeam Campaigns API endpoint
    """

    url = reverse('mi:sector_team_months', kwargs={'team_id': 1}) + "?year=2016"
    expected_response = {}

    def setUp(self):
        self.expected_response = {
            "avg_time_to_confirm": 0.0,
            "hvcs": {
                "campaigns": [
                    'HVC: E006',
                    'HVC: E019',
                    'HVC: E031',
                    'HVC: E072',
                    'HVC: E095',
                    'HVC: E115',
                    'HVC: E128',
                    'HVC: E160',
                    'HVC: E167',
                    'HVC: E191'
                ],
                "target": self.CAMPAIGN_TARGET * len(self.TEAM_1_HVCS)
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

    def test_sector_team_month_1(self):
        """ Tests covering SectorTeam Campaigns API endpoint """

        for i in range(4, 13):
            self._create_hvc_win(win_date=datetime.datetime(2016, i, 1))

        # Add few random ones
        self._create_hvc_win(win_date=datetime.datetime(2017, 1, 1))
        self._create_hvc_win(win_date=datetime.datetime(2016, 4, 1))
        self._create_hvc_win(win_date=datetime.datetime(2016, 5, 1))

        self.assertResponse()

    def test_sector_team_month_1_confirmed(self):
        """ Tests covering SectorTeam Campaigns API endpoint """

        for i in range(4, 13):
            self._create_hvc_win(win_date=datetime.datetime(2016, i, 1), confirm=True)

        # Add few random ones
        self._create_hvc_win(win_date=datetime.datetime(2017, 1, 1), confirm=True)
        self._create_hvc_win(win_date=datetime.datetime(2016, 4, 1), confirm=True)
        self._create_hvc_win(win_date=datetime.datetime(2016, 5, 1), confirm=True)

        self.expected_response["avg_time_to_confirm"] = 1.0
        self.expected_response["months"] = [
            {
                "date": "2016-04",
                "totals": {
                    "export": {
                        "hvc": {
                            "number": {
                                "confirmed": 2,
                                "total": 2,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 200000,
                                "total": 200000,
                                "unconfirmed": 0
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
                                "confirmed": 2,
                                "grand_total": 2,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 200000,
                                "grand_total": 200000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 2,
                            "total": 2,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 4600,
                            "total": 4600,
                            "unconfirmed": 0
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
                                "confirmed": 4,
                                "total": 4,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 400000,
                                "total": 400000,
                                "unconfirmed": 0
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
                                "confirmed": 4,
                                "grand_total": 4,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 400000,
                                "grand_total": 400000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 4,
                            "total": 4,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 9200,
                            "total": 9200,
                            "unconfirmed": 0
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
                                "confirmed": 5,
                                "total": 5,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 500000,
                                "total": 500000,
                                "unconfirmed": 0
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
                                "confirmed": 5,
                                "grand_total": 5,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 500000,
                                "grand_total": 500000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 5,
                            "total": 5,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 11500,
                            "total": 11500,
                            "unconfirmed": 0
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
                                "confirmed": 6,
                                "total": 6,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 600000,
                                "total": 600000,
                                "unconfirmed": 0
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
                                "confirmed": 6,
                                "grand_total": 6,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 600000,
                                "grand_total": 600000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 6,
                            "total": 6,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 13800,
                            "total": 13800,
                            "unconfirmed": 0
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
                                "confirmed": 7,
                                "total": 7,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 700000,
                                "total": 700000,
                                "unconfirmed": 0
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
                                "confirmed": 7,
                                "grand_total": 7,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 700000,
                                "grand_total": 700000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 7,
                            "total": 7,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 16100,
                            "total": 16100,
                            "unconfirmed": 0
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
                                "confirmed": 8,
                                "total": 8,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 800000,
                                "total": 800000,
                                "unconfirmed": 0
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
                                "confirmed": 8,
                                "grand_total": 8,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 800000,
                                "grand_total": 800000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 8,
                            "total": 8,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 18400,
                            "total": 18400,
                            "unconfirmed": 0
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
                                "confirmed": 9,
                                "total": 9,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 900000,
                                "total": 900000,
                                "unconfirmed": 0
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
                                "confirmed": 9,
                                "grand_total": 9,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 900000,
                                "grand_total": 900000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 9,
                            "total": 9,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 20700,
                            "total": 20700,
                            "unconfirmed": 0
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
                                "confirmed": 10,
                                "total": 10,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 1000000,
                                "total": 1000000,
                                "unconfirmed": 0
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
                                "confirmed": 10,
                                "grand_total": 10,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 1000000,
                                "grand_total": 1000000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 10,
                            "total": 10,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 23000,
                            "total": 23000,
                            "unconfirmed": 0
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
                                "confirmed": 11,
                                "total": 11,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 1100000,
                                "total": 1100000,
                                "unconfirmed": 0
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
                                "confirmed": 11,
                                "grand_total": 11,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 1100000,
                                "grand_total": 1100000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 11,
                            "total": 11,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 25300,
                            "total": 25300,
                            "unconfirmed": 0
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
                                "confirmed": 12,
                                "total": 12,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 1200000,
                                "total": 1200000,
                                "unconfirmed": 0
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
                                "confirmed": 12,
                                "grand_total": 12,
                                "unconfirmed": 0
                            },
                            "value": {
                                "confirmed": 1200000,
                                "grand_total": 1200000,
                                "unconfirmed": 0
                            }
                        }
                    },
                    "non_export": {
                        "number": {
                            "confirmed": 12,
                            "total": 12,
                            "unconfirmed": 0
                        },
                        "value": {
                            "confirmed": 27600,
                            "total": 27600,
                            "unconfirmed": 0
                        }
                    }
                }
            }
        ]
        self.assertResponse()

    def test_sector_team_month_1_some_wins_out_of_date(self):
        """ Check that out of date, wins that were added with date that is not within current financial year
        are not accounted for """

        for i in list(range(3, 13)) + [4, 5]:
            self._create_hvc_win(win_date=datetime.datetime(2016, i, 1))

        # add few more random financial year wins, both in and out
        for i in [6, 12]:
            self._create_hvc_win(win_date=datetime.datetime(2015, i, 1))

        for i in [1, 4, 8]:
            self._create_hvc_win(win_date=datetime.datetime(2017, i, 1))

            self.assertResponse()

    def test_months_no_wins(self):
        """
        Test, when there are no wins, that the response still spread across all the months from starting from
        financial start till today (frozen date), albeit all 0 numbers
        """

        def _setup_empty_months_response():
            """ Helper to build response """
            self.expected_response["months"] = []
            fin_year = FinancialYear.objects.get(id=2016)
            for item in month_iterator(get_financial_start_date(fin_year)):
                month_str = '{:d}-{:02d}'.format(*item)
                self.expected_response["months"].append({
                    "date": month_str,
                    "totals": {
                        "export": {
                            "hvc": {
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
                                    "grand_total": 0,
                                    "unconfirmed": 0
                                },
                                "value": {
                                    "confirmed": 0,
                                    "grand_total": 0,
                                    "unconfirmed": 0
                                }
                            }
                        },
                        "non_export": {
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
                        }
                    }
                })

        _setup_empty_months_response()
        self.assertResponse()

    def test_number_of_months_in_april(self):
        """
        Check that there will only be one month aggregated data when we are in April, financial year start -
        with one win
        """
        with freeze_time(self.fin_start_date):
            self._create_hvc_win(win_date=datetime.datetime(2016, 4, 1))
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 1)

    def test_number_of_months_in_april_confirmed(self):
        """
        Check that there will only be one month aggregated data when we are in April, financial year start -
        with one confirmed win
        """
        with freeze_time(self.fin_start_date):
            self._create_hvc_win(win_date=datetime.datetime(2016, 4, 1), confirm=True)
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 1)

    def test_number_of_months_in_april_no_wins(self):
        """
        Check that there will only be one month aggregated data when we are in April, financial year start -
        with no wins
        """
        with freeze_time(self.fin_start_date):
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 1)

    def test_number_of_months_in_march_with_wins(self):
        """
        Check that there will be 12 months aggregated data when we are in March, financial year end -
        with wins all the way
        """
        with freeze_time(self.fin_end_date):
            for i in range(4, 13):
                self._create_hvc_win(win_date=datetime.datetime(2016, i, 1))
            for i in range(1, 3):
                self._create_hvc_win(win_date=datetime.datetime(2017, i, 1))
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 12)

    def test_number_of_months_in_march_with_confirmed_wins(self):
        """
        Check that there will be 12 months aggregated data when we are in March, financial year end -
        with confirmed wins all the way
        """
        with freeze_time(self.fin_end_date):
            for i in range(4, 13):
                self._create_hvc_win(win_date=datetime.datetime(2016, i, 1), confirm=True)
            for i in range(1, 3):
                self._create_hvc_win(win_date=datetime.datetime(2017, i, 1), confirm=True)
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 12)

    def test_number_of_months_in_march_with_no_wins(self):
        """
        Check that there will be 12 months aggregated data when we are in March, financial year end -
        with no wins
        """
        with freeze_time(self.fin_end_date):
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 12)

    def test_number_of_months_in_april_non_hvc(self):
        """
        Check that there will only be one month aggregated data when we are in April, financial year start -
        with one non hvc win
        """
        with freeze_time(self.fin_start_date):
            self._create_non_hvc_win(win_date=datetime.datetime(2016, 4, 1))
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 1)

    def test_number_of_months_in_march_with_wins_non_hvc(self):
        """
        Check that there will be 12 months aggregated data when we are in March, financial year end -
        with non hvc wins all the way
        """
        with freeze_time(self.fin_end_date):
            for i in range(4, 13):
                self._create_non_hvc_win(win_date=datetime.datetime(2016, i, 1))
            for i in range(1, 3):
                self._create_non_hvc_win(win_date=datetime.datetime(2017, i, 1))
            api_response = self._get_api_response(self.url)
            response_decoded = json.loads(api_response.content.decode("utf-8"))["results"]
            self.assertEqual(len(response_decoded["months"]), 12)
