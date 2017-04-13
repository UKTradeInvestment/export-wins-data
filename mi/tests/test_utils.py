import json
from datetime import datetime

from django.test import TestCase

from freezegun import freeze_time

from mi.models import FinancialYear
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

    @freeze_time("2016-05-01")
    def test_financial_year_start_date(self):
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(get_financial_start_date(fin_year), datetime(2016, 4, 1))

    @freeze_time("2016-05-01")
    def test_financial_year_end_date(self):
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(get_financial_end_date(fin_year), datetime(2017, 3, 31))

    @freeze_time("2016-05-01")
    def test_month_iterator_with_current_date_as_end_date(self):
        months_in_fake_year = [(2016, 4), (2016, 5)]
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(list(month_iterator(get_financial_start_date(fin_year))), months_in_fake_year)

    @freeze_time("2016-05-01")
    def test_month_iterator(self):
        months_in_fake_year = [(2016, 4), (2016, 5), (2016, 6), (2016, 7), (2016, 8), (2016, 9),
                               (2016, 10), (2016, 11), (2016, 12), (2017, 1), (2017, 2), (2017, 3)]
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(list(month_iterator(get_financial_start_date(fin_year), get_financial_end_date(fin_year))),
                         months_in_fake_year)
