from io import StringIO
from random import randint
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from wins.factories import WinFactory
from wins.models import Win


class MockResponse:
    """Mock response for company matchin service."""

    def __init__(self, wins=[], match_id_none=False, status_code=200):
        """Init method with wins to populate the ids on the respose."""
        self.wins = wins
        self.status_code = status_code
        self.match_id_none = match_id_none

    def json(self):
        """Mock json method from request library."""
        if self.status_code == 400:
            return {
                "error": "Unable to read JSON payload",
            }

        if self.status_code > 400:
            return None

        generate_match = (lambda win: {
            "id": str(win.id),
            "match_id": None if self.match_id_none else randint(0, 100000),
            "similarity": "101000",
        })
        return {
            "matches": [generate_match(win) for win in self.wins],
        }


class ImportMatchIDsCommandTest(TestCase):
    """Testing import_match_ids Django management command."""

    def set_up_match_data(self):
        """Set up test."""
        self.return_value = MockResponse(wins=[WinFactory() for idx in range(200)])
        self.return_value_ids = [match.get("match_id") for match in self.return_value.json().get("matches")]

    @patch('requests.post')
    def test_command_output(self, mock_requests):
        """Test the import_match_ids command."""
        self.set_up_match_data()
        mock_requests.return_value = self.return_value
        call_command("import_match_ids")
        self.assertEqual(Win.objects.filter(match_id__isnull=False).count(), 200)
        mock_requests.assert_called_once()

    @patch('requests.post')
    def test_match_id_update(self, mock_requests):
        """Test the import_match_ids command."""
        self.set_up_match_data()
        mock_requests.return_value = self.return_value
        call_command("import_match_ids")
        self.assertEqual(Win.objects.filter(match_id__isnull=False).count(), 200)
        self.return_value.match_id_none = True
        call_command("import_match_ids")
        self.assertEqual(Win.objects.filter(match_id__isnull=True).count(), 200)

    @patch('requests.post')
    def test_match_id_error_400(self, mock_requests):
        """Test the import_match_ids command."""
        out = StringIO()
        mock_requests.return_value = MockResponse(status_code=400)

        with self.assertRaises(CommandError):
            call_command("import_match_ids", stdout=out)
            self.assertIn(
                "Error with the company matching service: HTTP STATUS 400 - Unable to read JSON payload",
                out.getvalue(),
            )

    @patch('requests.post')
    def test_match_id_error_500(self, mock_requests):
        """Test the import_match_ids command."""
        out = StringIO()
        mock_requests.return_value = MockResponse(status_code=500)

        with self.assertRaises(CommandError):
            call_command("import_match_ids", stdout=out)
            self.assertIn(
                "Error with the company matching service: HTTP STATUS 500",
                out.getvalue(),
            )
