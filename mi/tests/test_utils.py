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
