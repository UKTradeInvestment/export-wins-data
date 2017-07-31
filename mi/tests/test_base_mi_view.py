import datetime
import json
from django.http import QueryDict
from django.test import TestCase
from unittest.mock import MagicMock

from freezegun import freeze_time
from pytz import UTC
from rest_framework.renderers import JSONRenderer
from mi.tests.utils import datetime_factory, MIN, MAX
from mi.tests.base_test_case import MiApiViewsBaseTestCase
from mi.views.base_view import BaseMIView, BaseWinMIView


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class BaseTestCase(TestCase):

    def make_mock_request_for_year(self, year):
        fake_req = MagicMock()
        fake_req.GET = QueryDict("year={}".format(year), mutable=True)
        return fake_req

    def _render(self, data):
        return json.loads(JSONRenderer().render(data))


class BaseMIViewTestCase(BaseTestCase):

    def setUp(self):
        self.maxDiff = None
        self.view = BaseMIView()

    def test_handle_fin_year_valid(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        self.assertEqual(self.view.fin_year.id, 2017)

    def test_handle_fin_year_invalid(self):
        fake_req = self.make_mock_request_for_year(3333)
        mocked_not_found = self.view._not_found = MagicMock()

        self.view._handle_fin_year(fake_req)
        self.assertEqual(self.view.fin_year, None)
        self.assertEqual(mocked_not_found.call_count, 1)

    def test_date_range_start(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        start_date = self.view._date_range_start()
        self.assertEqual(start_date, datetime.datetime(2017, 4, 1, tzinfo=UTC))

    def test_date_range_end(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        end_date = self.view._date_range_end()
        self.assertEqual(end_date, MiApiViewsBaseTestCase.frozen_date_17)

    def test_fill_in_date_ranges(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        self.view._date_range_start = MagicMock(return_value='start')
        self.view._date_range_end = MagicMock(return_value='end')
        self.view._fill_date_ranges()

        self.assertEqual(
            self.view.date_range,
            {"start": "start", "end": "end"}
        )

    def test_handle_query_param_dates(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        fake_req.GET['date_start'] = '2017-8-1'
        fake_req.GET['date_end'] = '2017-9-1'
        self.view._handle_query_param_dates(fake_req)
        self.view._fill_date_ranges()

        self.assertEqual(
            self.view.date_range,
            {"start": datetime_factory(datetime.date(2017, 8, 1), MIN),
             "end": datetime_factory(datetime.date(2017, 9 , 1), MAX)}
        )

    def test_success(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        self.view._fill_date_ranges()
        resp = self.view._success([])

        self.assertEqual(
            set(resp.data.keys()),
            {
                'timestamp',
                'financial_year',
                'results',
                'date_range'
            }
        )

    def test_success_json(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        self.view._fill_date_ranges()
        resp = self.view._success([])
        jsonified_resp = self._render(resp.data)

        self.assertEqual(
            jsonified_resp,
            {
                'date_range': {
                    'end': '2017-05-01T00:00:00Z',
                    'start': '2017-04-01T00:00:00Z'
                },
                'financial_year': {
                    'description': '2017-18', 'id': 2017
                },
                'results': [],
                'timestamp': '2017-05-01T00:00:00Z'
            }
        )

    @freeze_time(MiApiViewsBaseTestCase.frozen_date)
    def test_success_json_2016(self):
        fake_req = self.make_mock_request_for_year(2016)
        self.view._handle_fin_year(fake_req)
        self.view._fill_date_ranges()
        resp = self.view._success([])
        jsonified_resp = self._render(resp.data)

        self.assertEqual(
            jsonified_resp,
            {
                'date_range': {
                    'end': '2016-11-01T00:00:00Z',
                    'start': '2016-04-01T00:00:00Z'
                },
                'financial_year': {
                    'description': '2016-17', 'id': 2016
                },
                'results': [],
                'timestamp': '2016-11-01T00:00:00Z'
            }
        )


class BaseWinMIViewTestCase(BaseTestCase):

    def setUp(self):
        self.maxDiff = None
        self.view = BaseWinMIView()

    def test_dates_passed_to_win_filter(self):
        fake_req = self.make_mock_request_for_year(2017)
        self.view._handle_fin_year(fake_req)
        fake_req.GET['date_start'] = '2017-8-1'
        fake_req.GET['date_end'] = '2017-9-1'
        self.view._handle_query_param_dates(fake_req)
        self.view._fill_date_ranges()

        start = datetime_factory(datetime.date(2017, 8, 1), MIN)
        end = datetime_factory(datetime.date(2017, 9 , 1), MAX)
        self.assertEqual(
            self.view.date_range,
            {"start": start, "end": end}
        )

        win_filter = self.view._wins_filter()
        filter_key, filter_params = win_filter.children[0] # first filtering of the win_filter
        self.assertEqual(filter_key, 'confirmation__created__range')
        self.assertEqual(filter_params, (start, end,))

