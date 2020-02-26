from django.test import TestCase
from wins.factories import WinFactory
from wins.match_id_utils import get_company_house_or_cdms_number, get_company_win_json
import json
import uuid


class MatchIDUtilsTestCase(TestCase):
    """Testing match ID utils helpers."""

    def test_get_company_house_or_cdms_number(self):
        """Test that get_company_house_or_cdms_number returns a company house number or cdms_number."""
        test_case = [
            ("00000000", {"company_house": "00000000"}),
            ("ABCDEFG", {"cdms_ref": "ABCDEFG"}),
            ("1234567", {"cdms_ref": "1234567"}),
            ("1234567A", {"cdms_ref": "1234567A"}),
            (None, {}),
            ('', {}),
        ]
        for test in test_case:
            (inputValue, expected) = test
            cdms_number_test = get_company_house_or_cdms_number(inputValue)
            self.assertEqual(cdms_number_test, expected)

    def test_get_company_win_json(self):
        """Test that get_company_win_json returns a valid payload to send to the company matching service."""
        win_args_1 = {
            "id": uuid.uuid4(),
            "cdms_reference": "01234567",
            "company_name": "Django Foundation",
            "customer_email_address": "noname@django.com",
        }

        win_args_2 = {
            "id": uuid.uuid4(),
            "cdms_reference": "ORG-01234567",
            "company_name": "Django Foundation",
            "customer_email_address": "noname@django.com",
        }

        win_args_3 = {
            "id": uuid.uuid4(),
            "cdms_reference": '',
            "company_name": "Django Foundation",
            "customer_email_address": "noname@django.com",
        }

        win_1 = WinFactory(**win_args_1)
        win_2 = WinFactory(**win_args_2)
        win_3 = WinFactory(**win_args_3)

        expected = {
            "descriptions": [
                {
                    "id": str(win_1.id),
                    "company_name": "Django Foundation",
                    "company_house": "01234567",
                    "contact_email": "noname@django.com",
                },
                {
                    "id": str(win_2.id),
                    "cdms_ref": "ORG-01234567",
                    "company_name": "Django Foundation",
                    "contact_email": "noname@django.com",
                },
                {
                    "id": str(win_3.id),
                    "company_name": "Django Foundation",
                    "contact_email": "noname@django.com",
                },
            ],
        }

        companies = [win_1, win_2, win_3]
        json_string = get_company_win_json(companies)
        json_data = json.loads(json_string)
        for win in companies:
            output_win = list(filter(lambda w: w.get('id') == str(win.id), json_data.get("descriptions")))[0]
            expected_win = list(filter(lambda w: w.get('id') == str(win.id), expected.get("descriptions")))[0]
            self.assertEqual(expected_win, output_win)
