from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from django_countries.fields import Country
from factory.fuzzy import FuzzyInteger, FuzzyChoice, FuzzyDate
from freezegun import freeze_time
from jmespath import search as s
from pytz import UTC

from wins.factories import NotificationFactory
from wins.models import Notification

c = datetime.combine
MIN = datetime.min.time()
MAX = datetime.max.time()

def datetime_factory(date, time):
    return c(date, time).replace(tzinfo=UTC)


class GenericTopNonHvcWinsTestMixin:
    """
    Mixin to test top_non_hvc views.
    The following must be defined in your `MiApiViewsWithWinsBaseTestCase` subclass:
        self.export_value - export value
        self.fin_years - list of years you want to test for e.g [2016,2017]
            * self.win_date_<year> - a win date for every year defined above
        self.view_base_url - url for your top_non_hvc_view without ?year= param
        self.TEST_COUNTRY_CODE - a country code
    """
    TEST_COUNTRY_CODE = "FR"
    fin_years = []

    def test_values_1_win(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self.url = self.get_url_for_year(year)
                w1 = self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=self.export_value,
                    country=self.TEST_COUNTRY_CODE
                )
                data = self._api_response_data

                # should be one sector
                self.assertEqual(len(data), 1)
                sector1 = data[0]

                # if there is only 1 win, it should be 100%
                self.assertEqual(sector1['averageWinPercent'], 100)

                # name is correctly translated
                c = Country(self.TEST_COUNTRY_CODE)
                self.assertEqual(sector1['region'], c.name)

                # sector matches win
                self.assertEqual(sector1['sector'], w1.get_sector_display())

                # should match value
                self.assertEqual(sector1['totalValue'], self.export_value)

                # should only be 1 win
                self.assertEqual(sector1['totalWins'], 1)

                # only 1 win so average should be same as total
                self.assertEqual(sector1['averageWinValue'], self.export_value)

                # only 1 win so average win percent should be 100%
                self.assertEqual(sector1['averageWinPercent'], 100)

    def test_annotated_total_value_top_non_hvc(self):
        """
        Check that annotation from database for total_value works
        """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                fuzz = FuzzyInteger(0, high=99999)
                exp_vals = [fuzz.fuzz() for _ in range(2)]
                win_date = getattr(self, f'win_date_{year}')
                # create two wins in same sector
                w1 = self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=exp_vals[0],
                    country=self.TEST_COUNTRY_CODE
                )
                self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=exp_vals[1],
                    country=self.TEST_COUNTRY_CODE,
                    sector_id=w1.sector,
                )

                data = self._api_response_data
                # should be one sector
                self.assertEqual(len(data), 1)
                sector1 = data[0]

                self.assertEqual(
                    sector1['totalValue'],
                    sum(exp_vals)
                )

    def test_annotated_count_top_non_hvc(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self.url = self.get_url_for_year(year)
                fuzz = FuzzyInteger(0, high=99999)
                exp_vals = [fuzz.fuzz() for _ in range(2)]

                # create two wins in same sector
                w1 = self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=exp_vals[0],
                    country=self.TEST_COUNTRY_CODE
                )
                self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=exp_vals[1],
                    country=self.TEST_COUNTRY_CODE,
                    sector_id=w1.sector,
                )

                data = self._api_response_data
                # should be one sector
                self.assertEqual(len(data), 1)
                sector1 = data[0]

                self.assertEqual(
                    sector1['totalWins'],
                    len(exp_vals)
                )

                other_sectors = set(
                    self._win_factory_function.sector_choices) - {w1.sector}

                w3_sector = FuzzyChoice(other_sectors).fuzz()
                exp_vals.append(fuzz.fuzz())

                w3 = self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=exp_vals[2],
                    country=self.TEST_COUNTRY_CODE,
                    sector_id=w3_sector,
                )

                data = self._api_response_data

                # should be two sectors
                self.assertEqual(len(data), 2)
                sector_with_2_wins = s("[?sector=='{}']|[0]".format(
                    w1.get_sector_display()), data)
                sector_with_1_win = s("[?sector=='{}']|[0]".format(
                    w3.get_sector_display()), data)
                self.assertEqual(sector_with_2_wins['totalWins'], 2)
                self.assertEqual(sector_with_1_win['totalWins'], 1)

    def test_non_hvc_order_by_value_desc(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                win_date = getattr(self, f'win_date_{year}')
                # create two wins in same sector
                w1 = self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=1,
                    country=self.TEST_COUNTRY_CODE
                )
                self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=1,
                    country=self.TEST_COUNTRY_CODE,
                    sector_id=w1.sector,
                )

                other_sectors = set(
                    self._win_factory_function.sector_choices) - {w1.sector}

                w3_sector = FuzzyChoice(other_sectors).fuzz()

                w3 = self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=10,
                    country=self.TEST_COUNTRY_CODE,
                    sector_id=w3_sector,
                )

                data = self._api_response_data
                self.assertEqual(len(data), 2)

                # sector with higher value should be first
                self.assertEqual(
                    data[0]['sector'],
                    w3.get_sector_display()
                )
                self.assertEqual(
                    data[1]['sector'],
                    w1.get_sector_display()
                )

                self.assertGreater(
                    data[0]['totalValue'],
                    data[1]['totalValue']
                )


class GenericWinTableTestMixin:
    """
    Mixin to test top_non_hvc views.
    The following must be defined in your `MiApiViewsWithWinsBaseTestCase` subclass:
        self.export_value - export value
        self.fin_years - list of years you want to test for e.g [2016,2017]
        self.win_date_2016 - a win date for 2016
        self.win_date_2017 - a win date for 2017
        self.view_base_url - url for your win_table without ?year= param
        self.TEST_HVC_CODE - hvc code to use for hvc wins e.g. E006
        self.TEST_COUNTRY_CODE - a country code
        self.expected_response - an expected response when no wins are created e.g:

            "os_region": {
                "id": str(self.test_region.id),
                "name": self.test_region.name,
            },
            "wins": {
                "hvc": []
            }
        }
    """

    export_value = 100000
    fin_years = [2016, 2017]
    TEST_CAMPAIGN_ID = 'E045'

    @property
    def dj_country(self):
        return Country(self.TEST_COUNTRY_CODE)

    def test_win_table_json_no_wins(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                self.assertResponse()

    def test_win_table_one_confirmed_hvc_win(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self._create_hvc_win(
                    hvc_code=self.TEST_CAMPAIGN_ID,
                    win_date=win_date,
                    response_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=self.export_value,
                    country=self.TEST_COUNTRY_CODE
                )
                self.url = self.get_url_for_year(year)
                api_response = self._api_response_data
                self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
                win_item = api_response["wins"]["hvc"][0]
                self.assertEqual(
                    win_item["hvc"]["code"], self.TEST_CAMPAIGN_ID)
                self.assertIsNotNone(win_item["win_date"])
                self.assertEqual(win_item["export_amount"], self.export_value)
                self.assertEqual(win_item["status"], "customer_confirmed")
                self.assertEqual(win_item["lead_officer"][
                                 "name"], "lead officer name")
                self.assertEqual(win_item["company"]["name"], "company name")
                self.assertEqual(win_item["company"][
                                 "cdms_id"], "cdms reference")
                self.assertTrue(win_item["credit"])

    def test_win_table_2017_one_unconfirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], self.TEST_CAMPAIGN_ID)
        self.assertIsNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "email_not_sent")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_one_unconfirmed_hvc_win_with_multiple_customer_notifications(self):
        win = self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )

        # add couple of customer notifications
        notify_date = self.win_date_2017 + timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        notify_date = self.win_date_2017 + timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)

    def test_win_table_2017_one_unconfirmed_hvc_win_with_multiple_mixed_notifications(self):
        win = self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )

        # add a customer notification
        notify_date = self.win_date_2017 + timedelta(days=1)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_CUSTOMER
        notification.created = notify_date
        notification.save()

        # add an officer notification
        notify_date = self.win_date_2017 + timedelta(days=2)
        notification = NotificationFactory(win=win)
        notification.type = Notification.TYPE_OFFICER
        notification.created = notify_date
        notification.save()

        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)

    def test_win_table_2017_one_confirmed_rejected_hvc_win(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=False,
            fin_year=2016,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], self.TEST_CAMPAIGN_ID)
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_rejected")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2017(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            agree_with_win=False,
            fin_year=2016,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["hvc"]) == 1)
        win_item = api_response["wins"]["hvc"][0]
        self.assertEqual(win_item["hvc"]["code"], self.TEST_CAMPAIGN_ID)
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_rejected")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])

    def test_win_table_2017_one_hvc_win_from_2016_confirmed_in_2016_no_result(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2016,
            response_date=self.win_date_2016,
            confirm=True,
            agree_with_win=False,
            fin_year=2016,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        self.assertResponse()

    def test_win_table_2017_confirmed_non_hvc(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["non_hvc"]) == 1)
        win_item = api_response["wins"]["non_hvc"][0]
        self.assertIsNotNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "customer_confirmed")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertTrue(win_item["credit"])

    def test_win_table_2017_unconfirmed_non_hvc(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=False,
            fin_year=2017,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["wins"]["non_hvc"]) == 1)
        win_item = api_response["wins"]["non_hvc"][0]
        self.assertIsNone(win_item["win_date"])
        self.assertEqual(win_item["export_amount"], self.export_value)
        self.assertEqual(win_item["status"], "email_not_sent")
        self.assertEqual(win_item["lead_officer"]["name"], "lead officer name")
        self.assertEqual(win_item["company"]["name"], "company name")
        self.assertEqual(win_item["company"]["cdms_id"], "cdms reference")
        self.assertFalse(win_item["credit"])


class GenericDetailsTestMixin:
    """
    Mixin to test Details views
        self.export_value - export value
        self.fin_years - list of years you want to test for e.g [2016,2017]
        self.win_date_2016 - a win date for 2016
        self.win_date_2017 - a win date for 2017
        self.view_base_url - url for your win_table without ?year= param
        self.TEST_HVC_CODE - hvc code to use for hvc wins e.g. E006
        self.TEST_COUNTRY_CODE - a country code
        self.expected_response - an expected response when no wins are created e.g:

            "post": {
                "id": self.TEST_TEAM['id'],
                "slug": slugify(self.TEST_TEAM['id']),
                "name": self.TEST_TEAM['name'],
            },
            "wins": {
                "hvc": []
                "non_hvc": []
            }
        }
    """

    export_value = 100000
    fin_years = [2016, 2017]
    TEST_CAMPAIGN_ID = 'E045'
    TEST_COUNTRY_CODE = 'FR'

    expected_response = {
        "wins": {
            "export": {
                "totals": {
                    "number": {
                        "grand_total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "value": {
                        "grand_total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                },
                "non_hvc": {
                    "number": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "value": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                },
                "hvc": {
                    "number": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "value": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                }
            },
            "non_export": {
                "number": {
                    "total": 0,
                    "unconfirmed": 0,
                    "confirmed": 0
                },
                "value": {
                    "total": 0,
                    "unconfirmed": 0,
                    "confirmed": 0
                }
            }
        },
        "avg_time_to_confirm": 0.0
    }

    def assert_top_level_keys(self, response_data):
        """
        takes response data and asserts top level keys.
        override this in your subclass. for example if you were
        testing a country view then you'd want to assert top level
        keys like the "name":
            self.assertEqual(response_data["name"], "France")
        :type response_data: dict
        """
        pass

    def assert_no_wins_no_values(self, response_data):

        self.assertEqual(response_data["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["totals"]["number"]["confirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["totals"]["value"]["confirmed"], 0)
        self.assertEqual(response_data["wins"]["export"]
                         ["totals"]["value"]["unconfirmed"], 0)

    def test_detail_json_YEAR_no_wins(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                self.assertResponse()
                self.assert_top_level_keys(self._api_response_data)

    def test_detail_YEAR_one_confirmed_hvc_win(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self._create_hvc_win(
                    hvc_code=self.TEST_CAMPAIGN_ID,
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=self.export_value,
                    country=self.TEST_COUNTRY_CODE
                )
                self.url = self.get_url_for_year(year)
                api_response = self._api_response_data
                self.assert_top_level_keys(api_response)
                self.assertEqual(api_response["wins"]["export"]
                                 ["hvc"]["number"]["confirmed"], 1)
                self.assertEqual(api_response["wins"]["export"]
                                 ["hvc"]["number"]["unconfirmed"], 0)
                self.assertEqual(
                    api_response["wins"]["export"]["hvc"]["value"]["confirmed"], self.export_value)
                self.assertEqual(api_response["wins"]["export"]
                                 ["hvc"]["value"]["unconfirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["number"]["confirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["number"]["unconfirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["value"]["confirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["value"]["unconfirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["totals"]["number"]["confirmed"], 1)
                self.assertEqual(api_response["wins"]["export"]
                                 ["totals"]["number"]["unconfirmed"], 0)
                self.assertEqual(
                    api_response["wins"]["export"]["totals"]["value"]["confirmed"], self.export_value)
                self.assertEqual(api_response["wins"]["export"]
                                 ["totals"]["value"]["unconfirmed"], 0)

    def test_detail_one_confirmed_YEAR_non_hvc_win_doesnt_appear_in_YEAR(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                win_date = getattr(self, f'win_date_{year}')
                self._create_non_hvc_win(
                    win_date=win_date,
                    confirm=True,
                    fin_year=year,
                    export_value=self.export_value,
                    country=self.TEST_COUNTRY_CODE
                )
                self.url = self.get_url_for_year(year)
                api_response = self._api_response_data
                self.assert_top_level_keys(api_response)
                self.assertEqual(api_response["wins"]["export"]
                                 ["hvc"]["number"]["confirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["hvc"]["number"]["unconfirmed"], 0)
                self.assertEqual(
                    api_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["hvc"]["value"]["unconfirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["number"]["confirmed"], 1)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["number"]["unconfirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["value"]["confirmed"], self.export_value)
                self.assertEqual(api_response["wins"]["export"]
                                 ["non_hvc"]["value"]["unconfirmed"], 0)
                self.assertEqual(api_response["wins"]["export"]
                                 ["totals"]["number"]["confirmed"], 1)
                self.assertEqual(api_response["wins"]["export"]
                                 ["totals"]["number"]["unconfirmed"], 0)
                self.assertEqual(
                    api_response["wins"]["export"]["totals"]["value"]["confirmed"], self.export_value)
                self.assertEqual(api_response["wins"]["export"]
                                 ["totals"]["value"]["unconfirmed"], 0)

    def test_detail_2016_only_hvc_win_confirmed_in_2017_appear_in_2017(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(
            api_response["wins"]["export"]["hvc"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(
            api_response["wins"]["export"]["totals"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["unconfirmed"], 0)

    def test_detail_one_confirmed_2016_hvc_win_doesnt_appear_in_2017(self):
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assert_top_level_keys(api_response)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["non_hvc"]["value"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["unconfirmed"], 0)


class GenericCampaignsViewTestCase:

    # defaults
    export_value = 100000
    fin_years = [2016, 2017]
    TEST_CAMPAIGN_ID = 'E045'
    TEST_COUNTRY_CODE = 'FR'

    def test_campaigns_json_YEAR_no_wins(self):
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                self.assertResponse()

    def test_avg_time_to_confirm_unconfirmed_wins(self):
        """ Average time to confirm will be zero, if there are no confirmed wins """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                win_date = getattr(self, f'win_date_{year}')

                for hvc_code in self.CEN_16_HVCS:
                    self._create_hvc_win(
                        hvc_code=hvc_code,
                        win_date=win_date,
                        confirm=False,
                        country=self.TEST_COUNTRY_CODE
                    )
                api_response = self._api_response_data
                expected_avg_time = 0.0
                response_avg_time = api_response["avg_time_to_confirm"]
                self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_nextday(self):
        """ Test average time to confirm when all wins confirmed in one day """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                win_date = getattr(self, f'win_date_{year}')

                for hvc_code in self.CEN_16_HVCS:
                    self._create_hvc_win(
                        hvc_code=hvc_code,
                        win_date=win_date,
                        notify_date=win_date,
                        response_date=win_date + timedelta(days=1),
                        confirm=True,
                        fin_year=year,
                        export_value=self.export_value,
                        country=self.TEST_COUNTRY_CODE
                    )
                api_response = self._api_response_data
                expected_avg_time = 1.0
                response_avg_time = api_response["avg_time_to_confirm"]
                self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_randomly(self):
        """
        Average time to confirm should be more than one,
        when wins took more than one day to be confirmed
        """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                win_date = getattr(self, f'win_date_{year}')
                for hvc_code in self.CEN_16_HVCS:
                    response_date = FuzzyDate(win_date + timedelta(days=2),
                                              win_date + timedelta(days=5)
                                              ).evaluate(2, None, False)
                    self._create_hvc_win(
                        hvc_code=hvc_code,
                        win_date=win_date,
                        notify_date=win_date,
                        response_date=response_date,
                        confirm=True,
                        fin_year=year,
                        export_value=self.export_value,
                        country=self.TEST_COUNTRY_CODE
                    )

                api_response = self._api_response_data
                response_avg_time = api_response["avg_time_to_confirm"]
                self.assertTrue(response_avg_time > 1.0)

    def test_campaigns_count_no_wins(self):
        """ Make sure number of campaigns returned have no effect when there are no wins """
        for year in self.fin_years:
            with self.subTest(year=year):
                self.url = self.get_url_for_year(year)
                api_response = self._api_response_data
                self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaign_hvc_number_unconfirmed_wins(self):
        """ Check HVC number with unconfirmed HVC wins """

        self.url = self.get_url_for_year(2017)
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country=self.TEST_COUNTRY_CODE
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)

    def test_campaign_hvc_number_mixed_wins(self):
        """ Check HVC numbers with both confirmed and unconfirmed HVC wins """

        self.url = self.get_url_for_year(2017)
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 20)

    def test_campaign_hvc_value_unconfirmed_wins(self):
        """ Check HVC value when there are unconfirmed wins """
        self.url = self.get_url_for_year(2017)
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 10)

    def test_campaign_hvc_value_confirmed_wins(self):
        """ Check HVC value when there are confirmed wins """
        self.url = self.get_url_for_year(2017)
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 10)

    def test_campaign_hvc_value_mixed_wins(self):
        """ Check HVC value when there are both confirmed and unconfirmed wins """
        self.url = self.get_url_for_year(2017)
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        for _ in range(10):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country=self.TEST_COUNTRY_CODE
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], self.export_value * 20)


class GenericMonthlyViewTestCase:

    # defaults
    export_value = 100000
    fin_years = [2016, 2017]
    TEST_CAMPAIGN_ID = 'E045'
    TEST_COUNTRY_CODE = 'FR'

    def test_get_with_no_data(self):
        self.url = self.get_url_for_year(2017)
        data = self._api_response_data

        # there should be no wins
        number_of_wins = s('sum(months[].totals.*[].*[].number.*[])', data)
        self.assertEqual(number_of_wins, 0)

        # every value in the wins breakdown should be 0
        value_of_wins = s('sum(months[].totals.*[].*[].*[].*[])', data)
        self.assertEqual(value_of_wins, 0)

    def test_get_with_1_win(self):

        w = self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID, win_date=now(), response_date=now(),
            confirm=True, fin_year=2017, export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE)

        self.url = self.get_url_for_year(2017)
        data = self._api_response_data
        year = w.created.year
        month = w.created.month

        number_of_wins_this_month = s(
            f"months[?date=='{year}-{month:02d}'].totals.export.hvc.number.total | [0]", data)
        number_of_wins_last_month = s(
            f"months[?date=='{year}-{month - 1:02d}'].totals.export.hvc.number.total | [0]", data)

        # there should be no wins for 'last' month
        self.assertEqual(number_of_wins_last_month, 0)

        # there should be 1 for this month
        self.assertEqual(number_of_wins_this_month, 1)

        # value should match the win we created
        value_of_wins = s("sum(months[].totals.export.hvc.value.total)", data)
        self.assertEqual(value_of_wins, self.export_value)

    def test_group_by_month_from_data(self):

        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID, win_date=now(), response_date=now(),
            confirm=True, fin_year=2017, export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE)

        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID, win_date=now() + relativedelta(months=-1),
            confirm=True, fin_year=2017, export_value=self.export_value,
            country=self.TEST_COUNTRY_CODE)

        self.url = self.get_url_for_year(2017)
        data = self._api_response_data

        number_of_wins_2017_05 = s(
            "months[?date=='2017-05'].totals.export.hvc.number.total | [0]", data)
        number_of_wins_2017_04 = s(
            "months[?date=='2017-04'].totals.export.hvc.number.total | [0]", data)

        # there should be no wins for 'last' month
        self.assertEqual(number_of_wins_2017_04, 1)

        # there should be 2 for this month (cumulative) take the one
        # from last month and add to the one from this month
        self.assertEqual(number_of_wins_2017_05, 2)

        # value should match the win we created for
        # month 1, then 2x value for month 2 therefore
        # sum of all totals will be 3x export_value
        value_of_wins = s("sum(months[].totals.export.hvc.value.total)", data)
        self.assertEqual(value_of_wins, self.export_value * 3)
