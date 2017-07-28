from datetime import datetime, date

from django.test import SimpleTestCase

from mi.serializers import DateRangeSerializer


class FakeFinancialYear(object):
    start = datetime.combine(date(2017, 4, 1), datetime.min.time())
    end = datetime.combine(date(2018, 3, 31), datetime.max.time())

class DateRangeSerializerTestCase(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.FAKE_YEAR = FakeFinancialYear()

    def test_parses_datetime_start_and_end(self):
        input_data = {'2017-4-'}
        expected_data = {}
        s = DateRangeSerializer(financial_year=self.FAKE_YEAR)

        pass

    def test_parses_datetime_only_start_no_end(self):
        pass

    def test_parses_datetime_only_end_no_start(self):
        pass

    def test_parses_date_start_and_end(self):
        pass

    def test_parses_date_only_start_no_end(self):
        pass

    def test_parses_date_only_end_no_start(self):
        pass
