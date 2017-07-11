from datetime import datetime

from django.test import TestCase

from freezegun import freeze_time

from mi.models import FinancialYear
from mi.utils import month_iterator


class UtilTests(TestCase):
    frozen_date = "2016-11-01"

    @freeze_time("2016-05-01")
    def test_financial_year_start_date(self):
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(fin_year.start, datetime(2016, 4, 1))

    @freeze_time("2016-05-01")
    def test_financial_year_end_date(self):
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(fin_year.end, datetime(2017, 3, 31, 23, 59, 59))

    @freeze_time("2016-05-01")
    def test_month_iterator_with_current_date_as_end_date(self):
        months_in_fake_year = [(2016, 4), (2016, 5)]
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(list(month_iterator(fin_year)), months_in_fake_year)

    @freeze_time("2017-05-01")
    def test_month_iterator(self):
        months_in_fake_year = [(2016, 4), (2016, 5), (2016, 6), (2016, 7), (2016, 8), (2016, 9),
                               (2016, 10), (2016, 11), (2016, 12), (2017, 1), (2017, 2), (2017, 3)]
        fin_year = FinancialYear.objects.get(id=2016)
        self.assertEqual(list(month_iterator(fin_year)),
                         months_in_fake_year)
