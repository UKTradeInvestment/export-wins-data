import datetime

from django.core.management import call_command
from django.urls import reverse
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now, get_current_timezone

from factory.fuzzy import FuzzyDate
from django_countries.fields import Country as DjangoCountry
from freezegun import freeze_time
from jmespath import search as s

from fixturedb.factories.win import create_win_factory

from mi.models import Country
from mi.tests.base_test_case import (
    MiApiViewsWithWinsBaseTestCase,
    MiApiViewsBaseTestCase
)
from mi.utils import sort_campaigns_by
from mi.tests.utils import GenericTopNonHvcWinsTestMixin, GenericWinTableTestMixin, GenericMonthlyViewTestCase


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class CountryBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):
    export_value = 100000
    win_date_2017 = datetime.datetime(
        2017, 4, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(
        2016, 5, 25, tzinfo=get_current_timezone())
    fy_2016_last_date = datetime.datetime(
        2017, 3, 31, tzinfo=get_current_timezone())

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)


class CountryDetailTestCase(CountryBaseViewTestCase):
    TEST_COUNTRY_CODE = "FR"
    country_detail_url = reverse(
        'mi:country_detail', kwargs={"country_code": "FR"})
    country_detail_url_invalid = reverse(
        'mi:country_detail', kwargs={"country_code": "ABC"})

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.country_detail_url

    def test_2017_detail_in_2016_404(self):
        self.view_base_url = self.country_detail_url_invalid
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_detail_in_2017_404(self):
        self.view_base_url = self.country_detail_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_detail_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "name": "France",
            "id": "FR",
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
            "hvcs": {
                "campaigns": [
                    'HVC: E045',
                    'HVC: E046',
                    'HVC: E047',
                    'HVC: E048',
                    'HVC: E214'
                ],
                "target": 50000000
            },
            "avg_time_to_confirm": 0.0
        }
        self.assertResponse()

    def test_detail_json_2017_no_wins(self):
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "name": "France",
            "id": "FR",
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
            "hvcs": {
                "campaigns": ['E04517', 'E04617', 'E04717'],
                "target": 110000000
            },
            "avg_time_to_confirm": 0.0
        }
        self.assertResponse()

    def test_detail_one_confirmed_2016_hvc_win_doesnt_appear_in_2016(self):
        self._create_hvc_win(
            hvc_code='E045',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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

    def test_detail_2017_one_confirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E045',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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
            hvc_code='E045',
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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

    def test_detail_one_unconfirmed_2016_hvc_win_appear_in_2017(self):
        self._create_hvc_win(
            hvc_code='E045',
            win_date=self.win_date_2016,
            confirm=False,
            fin_year=2016,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["unconfirmed"], 1)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["value"]["confirmed"], 0)
        self.assertEqual(
            api_response["wins"]["export"]["hvc"]["value"]["unconfirmed"], self.export_value)
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
                         ["totals"]["number"]["unconfirmed"], 1)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]["totals"]
                         ["value"]["unconfirmed"], self.export_value)

    def test_detail_one_2016_common_hvc_win_confirmed_in_2017_appear_in_2017(self):
        self._create_hvc_win(
            hvc_code='E045',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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

    def test_detail_2016_only_hvc_win_confirmed_in_2017_appear_in_2017(self):
        self._create_hvc_win(
            hvc_code='E046',
            win_date=self.win_date_2016,
            response_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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

    def test_detail_2017_one_confirmed_diff_hvc_win_for_FR_appears(self):
        self._create_hvc_win(
            hvc_code='E001',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(
            api_response["wins"]["export"]["hvc"]["value"]["confirmed"], 0)
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
        self.assertEqual(
            api_response["wins"]["export"]["totals"]["value"]["confirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["unconfirmed"], 0)

    def test_detail_FR_hvc_win_but_not_FR_doesnt_appear(self):
        self._create_hvc_win(
            hvc_code='E045',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='CA'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["number"]["unconfirmed"], 0)
        self.assertEqual(api_response["wins"]["export"]
                         ["hvc"]["value"]["confirmed"], self.export_value)
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
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["confirmed"], self.export_value)
        self.assertEqual(api_response["wins"]["export"]
                         ["totals"]["value"]["unconfirmed"], 0)

    def test_detail_one_confirmed_2016_non_hvc_win_doesnt_appear_in_2016(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2016,
            confirm=True,
            fin_year=2016,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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

    def test_detail_2017_one_confirmed_non_hvc_win(self):
        self._create_non_hvc_win(
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
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


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class CountriesMonthsTestCase(CountryBaseViewTestCase, GenericMonthlyViewTestCase):

    export_value = 123456
    TEST_CAMPAIGN_ID = 'E045'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.test_country = Country.objects.get(country='FR')
        self.view_base_url = reverse('mi:country_monthly', kwargs={
                                     'country_code': self.test_country.country})


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class CountryCampaignsTestCase(CountryBaseViewTestCase):
    list_countries_base_url = reverse('mi:countries')
    view_base_url = reverse('mi:country_campaigns', kwargs={
        'country_code': "FR"})
    CEN_2016_HVCS = ["E045", "E046", "E047", "E048", "E214"]
    CEN_2017_HVCS = ["E045", "E046", "E047", "E054", "E119", "E225"]
    FR_2017_HVCS = ["E045", "E046", "E047"]
    TEST_CAMPAIGN_ID = "E045"
    TARGET_E017 = 10000000
    PRORATED_TARGET = 833333  # target based on the frozen date

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.url = self.get_url_for_year(2017)

    def test_campaigns_list_2016(self):
        self.url = self.get_url_for_year(2016)
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), len(
            api_response["hvcs"]["campaigns"]))
        self.assertEqual(
            len(api_response["campaigns"]), len(self.CEN_2016_HVCS))

    def test_campaigns_2016_no_duplicates(self):
        list_countries_url = self.get_url_for_year(
            year=2016, base_url=self.list_countries_base_url)
        all_countries = self._get_api_response(
            list_countries_url).data["results"]
        for country in all_countries:
            country_url = reverse('mi:country_campaigns',
                                  kwargs={"country_code": country["id"]})
            self.url = self.get_url_for_year(2016, base_url=country_url)
            api_response = self._api_response_data
            for campaign in api_response["campaigns"]:
                dups = s("campaigns[?campaign_id=='{}'].campaign".format(
                    campaign["campaign_id"]), api_response)
                self.assertTrue(len(dups) == 1)

    def test_campaigns_list_2017(self):
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaigns_list_2017_no_duplicates(self):
        list_countries_url = self.get_url_for_year(
            year=2017, base_url=self.list_countries_base_url)
        all_countries = self._get_api_response(
            list_countries_url).data["results"]
        for country in all_countries:
            country_url = reverse('mi:country_campaigns',
                                  kwargs={"country_code": country["id"]})
            self.url = self.get_url_for_year(2017, base_url=country_url)
            api_response = self._api_response_data
            for campaign in api_response["campaigns"]:
                dups = s("campaigns[?campaign_id=='{}'].campaign".format(
                    campaign["campaign_id"]), api_response)
                self.assertTrue(len(dups) == 1)

    def test_campaigns_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "campaigns": [],
            "name": "France",
            "id": "FR",
            "hvcs": {
                "campaigns": [
                    "HVC: E045",
                    "HVC: E046",
                    "HVC: E047",
                    "HVC: E048",
                    "HVC: E214",
                ],
                "target": self.CAMPAIGN_TARGET * len(self.CEN_2016_HVCS)
            },
            "avg_time_to_confirm": 0
        }
        campaigns = []
        for hvc_code in self.CEN_2016_HVCS:
            campaigns.append({
                "campaign": "HVC",
                "campaign_id": hvc_code,
                "totals": {
                    "hvc": {
                        "value": {
                            "unconfirmed": 0,
                            "confirmed": 0,
                            "total": 0
                        },
                        "number": {
                            "unconfirmed": 0,
                            "confirmed": 0,
                            "total": 0
                        }
                    },
                    "change": "up",
                    "progress": {
                        "unconfirmed_percent": 0,
                        "confirmed_percent": 0,
                        "status": "red"
                    },
                    "target": self.CAMPAIGN_TARGET
                }
            })

        self.expected_response["campaigns"] = sorted(
            campaigns, key=sort_campaigns_by, reverse=True)
        self.assertResponse()

    def test_avg_time_to_confirm_unconfirmed_wins(self):
        """ Average time to confirm will be zero, if there are no confirmed wins """
        for hvc_code in self.CEN_2016_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code, confirm=False, country="FR")
        api_response = self._api_response_data
        expected_avg_time = 0.0
        response_avg_time = api_response["avg_time_to_confirm"]
        self.assertEqual(expected_avg_time, response_avg_time)

    def test_avg_time_to_confirm_wins_confirmed_nextday(self):
        """ Test average time to confirm when all wins confirmed in one day """
        for hvc_code in self.CEN_2016_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                notify_date=self.win_date_2017,
                response_date=self.win_date_2017 + datetime.timedelta(days=1),
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='FR'
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
        for hvc_code in self.CEN_2016_HVCS:
            response_date = FuzzyDate(datetime.datetime(2017, 5, 27),
                                      datetime.datetime(2017, 5, 31)).evaluate(2, None, False)
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                notify_date=self.win_date_2017,
                response_date=response_date,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='FR'
            )

        api_response = self._api_response_data
        response_avg_time = api_response["avg_time_to_confirm"]
        self.assertTrue(response_avg_time > 1.0)

    def test_campaigns_count_no_wins(self):
        """ Make sure number of campaigns returned have no effect when there are no wins """
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaigns_count_unconfirmed_wins(self):
        """ unconfirmed wins shouldn't have any effect on number of campaigns """
        for hvc_code in self.CEN_2017_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaigns_count_confirmed_wins(self):
        """ confirmed HVC wins shouldn't have any effect on number of campaigns """
        for hvc_code in self.CEN_2017_HVCS:
            self._create_hvc_win(
                hvc_code=hvc_code,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country='FR'
            )

        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaigns_count_unconfirmed_nonhvc_wins(self):
        """ unconfirmed non-hvc wins shouldn't have any effect on number of campaigns """
        for _ in self.CEN_2017_HVCS:
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=self.export_value,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaigns_count_confirmed_nonhvc_wins(self):
        """ confirmed non-hvc wins shouldn't have any effect on number of campaigns """
        for _ in self.CEN_2017_HVCS:
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=self.export_value,
                country="FR"
            )
        api_response = self._api_response_data
        self.assertEqual(len(api_response["campaigns"]), 5)

    def test_campaign_progress_colour_no_wins(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are no wins """
        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_unconfirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are no confirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=100000,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_confirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are not enough confirmed wins """
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=100000,
            country='FR'
        )
        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_nonhvc_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are only non-hvc wins """
        for _ in range(1, 11):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=100000,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_nonhvc_confirmed_wins_red(self):
        """ Given the 'Frozen datetime', progress colour will be Red if there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=100000,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_colour_confirmed_wins_amber(self):
        """
        Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        export_val = self.PRORATED_TARGET * 30 / 100
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=export_val,
            country='FR'
        )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "amber")

    def test_campaign_progress_confirmed_wins_50_green(self):
        """ Progress colour should be green if there are enough win to take runrate past 45% """
        for _ in range(1, 5):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=3000000,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "green")

    def test_campaign_progress_confirmed_wins_45_green(self):
        """ Boundary Testing for Green:
        Progress colour should be green if there are enough win to take runrate past 45% """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=791700,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "green")

    def test_campaign_progress_confirmed_wins_44_amber(self):
        """
        Boundary testing for Amber: Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        export_val = self.PRORATED_TARGET * 44 / 100
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=export_val / 10,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "amber")

    def test_campaign_progress_confirmed_wins_25_amber(self):
        """
        Boundary testing for Amber: Given the 'Frozen datetime', progress colour will be Amber
        if there only few confirmed wins to take runrate past 25% but still less than 45%
        """
        export_val = self.PRORATED_TARGET * 25 / 100
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=export_val / 10,
                country='FR'
            )
            self._create_hvc_win(hvc_code=self.TEST_CAMPAIGN_ID,
                                 export_value=146700, confirm=True)

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "amber")

    def test_campaign_progress_confirmed_wins_24_red(self):
        """ Boundary testing for red: Anything less than 25% runrate of progress should be Red """
        export_val = self.PRORATED_TARGET * 24 / 100
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=export_val / 10,
                country='FR'
            )

        api_response = self._api_response_data
        e017_status = s("campaigns[?campaign_id=='{}'].totals.progress.status".format(self.TEST_CAMPAIGN_ID),
                        api_response)[0]
        self.assertEqual(e017_status, "red")

    def test_campaign_progress_percent_no_wins(self):
        """ Progress percentage will be 0, if there are no confirmed HVC wins """
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_unconfirmed_wins(self):
        """ Progress percentage will be 0, if there are no confirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=100000,
                country='FR'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10.0)

    def test_campaign_progress_percent_confirmed_wins_1(self):
        """ Test simple progress percent """
        self._create_hvc_win(
            hvc_code=self.TEST_CAMPAIGN_ID,
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=100000,
            country='FR'
        )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 1.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_nonhvc_wins(self):
        """ Non hvc wins shouldn't effect progress percent """
        for _ in range(1, 11):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=100000,
                country='FR'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_nonhvc_confirmed_wins(self):
        """ Non hvc confirmed wins shouldn't effect progress percent """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_progress_percent_confirmed_wins_20(self):
        """ Check 20% progress percent """
        for _ in range(1, 3):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=1000000,
                country='FR'
            )

        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.confirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 20.0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.progress.unconfirmed_percent"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0.0)

    def test_campaign_hvc_number_no_wins(self):
        """ HVC number shouldn't be affected when there are no wins """
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_number_only_nonhvc_wins(self):
        """ HVC number shouldn't be affected when there are only non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_number_only_nonhvc_confirmed_wins(self):
        """ HVC number shouldn't be affected when there are only confirmed non-hvc wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_number_unconfirmed_wins(self):
        """ Check HVC number with unconfirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)

    def test_campaign_hvc_number_confirmed_wins(self):
        """ Check HVC number with confirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)

    def test_campaign_hvc_number_mixed_wins(self):
        """ Check HVC numbers with both confirmed and unconfirmed HVC wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 10)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.number.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 20)

    def test_campaign_hvc_value_no_wins(self):
        """ HVC value will be 0 with there are no wins """
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_value_only_nonhvc_wins(self):
        """ HVC value will be 0 there are only unconfirmed non-HVC wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_value_only_nonhvc_confirmed_wins(self):
        """ HVC value will be 0 when there are only confirmed non-HVC wins """
        for _ in range(1, 10):
            self._create_non_hvc_win(
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)

    def test_campaign_hvc_value_unconfirmed_wins(self):
        """ Check HVC value when there are unconfirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)

    def test_campaign_hvc_value_confirmed_wins(self):
        """ Check HVC value when there are confirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 0)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)

    def test_campaign_hvc_value_mixed_wins(self):
        """ Check HVC value when there are both confirmed and unconfirmed wins """
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=False,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        for _ in range(1, 11):
            self._create_hvc_win(
                hvc_code=self.TEST_CAMPAIGN_ID,
                win_date=self.win_date_2017,
                confirm=True,
                fin_year=2017,
                export_value=300000,
                country='FR'
            )
        api_response = self._api_response_data
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.confirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.unconfirmed"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 3000000)
        self.assertEqual(s("campaigns[?campaign_id=='{}'].totals.hvc.value.total"
                           .format(self.TEST_CAMPAIGN_ID), api_response)[0], 6000000)


class CountryTopNonHVCViewTestCase(CountryBaseViewTestCase, GenericTopNonHvcWinsTestMixin):

    export_value = 9992

    TEST_COUNTRY_CODE = "FR"
    country_top_nonhvc_url = reverse(
        'mi:country_top_nonhvc', kwargs={"country_code": "FR"})
    country_topnonhvc_url_invalid = reverse(
        'mi:country_top_nonhvc', kwargs={"country_code": "ABC"})
    country_topnonhvc_url_missing_country_kwarg = reverse(
        'mi:country_top_nonhvc', kwargs={"country_code": None})

    fin_years = [2016, 2017]

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.country_top_nonhvc_url

    def test_fake_country_404(self):
        self.view_base_url = self.country_topnonhvc_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_missing_country_404(self):
        self.view_base_url = self.country_topnonhvc_url_missing_country_kwarg
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)


class CountryWinTableTestCase(CountryBaseViewTestCase, GenericWinTableTestMixin):

    TEST_COUNTRY_CODE = 'FR'
    TEST_COUNTRY = DjangoCountry(TEST_COUNTRY_CODE)
    fin_years = [2016, 2017]

    expected_response = {
        "country": {
            "id": TEST_COUNTRY_CODE,
            "name": TEST_COUNTRY.name,
        },
        "wins": {
            "hvc": []
        }

    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.country_win_table_url = reverse('mi:country_win_table', kwargs={
            'country_code': self.TEST_COUNTRY_CODE
        })
        self.country_win_table_url_invalid = reverse('mi:country_win_table', kwargs={
            'country_code': 'XX'
        })
        self.view_base_url = self.country_win_table_url
