
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator

from wins.match_id_utils import request_match_ids
from wins.models import Win


class Command(BaseCommand):
    """Command class for importing match IDs from the company matching service."""

    help = 'Imports match ids from the company matching service'

    def save_match_id(self, wins):
        """Save the match id."""
        response = request_match_ids(wins)
        if response.status_code >= 400:
            error_message = f"HTTP STATUS {response.status_code}"
            if response.status_code == 400:
                error = response.json()
                error_message = f"{error_message} - {error.get('error', '')}"
            raise CommandError(f"Error with the company matching service: {error_message}")

        if response.status_code == 200:
            matches = response.json()
            for company in matches.get('matches', []):
                match_id = company.get('match_id')
                id = company.get('id')
                win = Win.objects.get(pk=id)
                win.match_id = match_id
                win.save()

    def handle(self, *args, **options):
        """Execute command."""
        p = Paginator(Win.objects.all(), 10000)
        for page_number in p.page_range:
            page = p.page(page_number)
            self.save_match_id(page.object_list)
        self.stdout.write(self.style.SUCCESS("Match ids successfully updated."))
