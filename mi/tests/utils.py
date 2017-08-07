from datetime import datetime, timedelta

from django.utils.functional import cached_property
from django_countries.fields import Country
from factory.fuzzy import FuzzyInteger, FuzzyChoice
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
        self.view_base_url - url for your top_non_hvc_view without ?year= param
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
