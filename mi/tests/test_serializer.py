from datetime import date

from django.test import SimpleTestCase

from mi.serializers import DateRangeSerializer
from mi.tests.utils import datetime_factory, MIN, MAX


class FakeFinancialYear(object):
    start = datetime_factory(date(2017, 4, 1), MIN)
    end = datetime_factory(date(2018, 3, 31), MAX)


class DateRangeSerializerTestCase(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.FAKE_YEAR = FakeFinancialYear()

    def test_parses_datetime_start_and_end(self):
        input_data = {
            'date_start': '2017-4-1T00:00Z',
            'date_end': '2017-4-2T23:59:59.999999Z'
        }
        expected_data = {
            'date_start': datetime_factory(date(2017, 4, 1), MIN),
            'date_end': datetime_factory(date(2017, 4, 2), MAX),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_parses_datetime_only_start_no_end(self):
        input_data = {
            'date_start': '2017-4-1T00:00Z',
        }
        expected_data = {
            'date_start': datetime_factory(date(2017, 4, 1), MIN),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_parses_datetime_only_end_no_start(self):
        input_data = {
            'date_end': '2017-4-2T23:59:59.999999Z'
        }
        expected_data = {
            'date_end': datetime_factory(date(2017, 4, 2), MAX),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_parses_date_start_and_end(self):
        input_data = {
            'date_start': '2017-4-1',
            'date_end': '2017-4-2'
        }
        expected_data = {
            'date_start': datetime_factory(date(2017, 4, 1), MIN),
            'date_end': datetime_factory(date(2017, 4, 2), MAX),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_parses_date_only_start_no_end(self):
        input_data = {
            'date_start': '2017-4-1',
        }
        expected_data = {
            'date_start': datetime_factory(date(2017, 4, 1), MIN),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_parses_date_only_end_no_start(self):
        input_data = {
            'date_end': '2017-4-2'
        }
        expected_data = {
            'date_end': datetime_factory(date(2017, 4, 2), MAX),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_no_inputs_is_valid(self):
        input_data = {}
        expected_data = {}

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_ignores_extra_inputs_is_valid(self):
        input_data = {'foo': 'bar'}
        expected_data = {}

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

        input_data = {
            'date_start': '2017-4-1',
            'date_end': '2017-4-2',
            'foo': 'bar'
        }
        expected_data = {
            'date_start': datetime_factory(date(2017, 4, 1), MIN),
            'date_end': datetime_factory(date(2017, 4, 2), MAX),
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertTrue(s.is_valid())
        self.assertDictEqual(s.validated_data, expected_data)

    def test_invalid_start_date_format_returns_format_error(self):
        input_data = {
            'date_start': '2017.4.1',
        }

        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertFalse(s.is_valid())
        self.assertTrue('date_start' in s.errors)
        self.assertTrue('format' in s.errors['date_start'][0])

    def test_invalid_end_date_format_returns_format_error(self):
        input_data = {
            'date_end': '2017.4.1',
        }
        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertFalse(s.is_valid())
        self.assertTrue('date_end' in s.errors)
        self.assertTrue('format' in s.errors['date_end'][0])

    def test_invalid_start_and_end_date_format_returns_both_format_errors(self):
        input_data = {
            'date_start': '207.4.1',
            'date_end': '2017.4.1',
        }
        s = DateRangeSerializer(financial_year=self.FAKE_YEAR, data=input_data)
        self.assertFalse(s.is_valid())
        self.assertTrue('date_start' in s.errors)
        self.assertTrue('format' in s.errors['date_start'][0])
        self.assertTrue('date_end' in s.errors)
        self.assertTrue('format' in s.errors['date_end'][0])
