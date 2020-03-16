import logging
import time

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator

from wins.company_matching_utils import (
    CompanyMatchingServiceConnectionError,
    CompanyMatchingServiceHTTPError,
    CompanyMatchingServiceTimeoutError,
    update_match_ids,
)
from wins.models import Win

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Command class for importing match IDs from the company matching service.
    match ids are used as an company identifier for external services.
    The command will ideally be ran once then future records will be updated with a post save
    signal.
    """

    help = 'Imports and updates match ids to a win records from the company matching service'

    def _import_match_ids(self, wins):
        """
        Get match ids with a wins a list of wins.
        Raises a CommandError is the call the the company matching service fails
        """
        try:
            response = update_match_ids(wins)
            return response.json()
        except (
            CompanyMatchingServiceConnectionError,
            CompanyMatchingServiceTimeoutError,
        ) as e:
            message = f'Error importing match ids due to a client error: {str(e)}'
            self.style.ERROR(message)
            raise CommandError(message) from e
        except CompanyMatchingServiceHTTPError as e:
            message = f'Error importing match ids due to an HTTP Error: {str(e)}'
            self.style.ERROR(message)
            raise CommandError(message) from e

    def _save_match_ids_to_models(self, json_response):
        """
        Save match ID to the win record.
        The id is the uuid that was passed in the request, the company matching api
        echos the ID to allow the service to map the match_id to a record.
        The json_response is in the format below
        {
            "matches": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "match_id": 1,
                    "similarity": "100000"
                },
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "match_id": 1,
                    "similarity": "110000"
                }
            ]
        }
        """
        for company in json_response.get('matches', []):
            """
            Save match_id from the json response. If no match is found set the field to None.
            The reason we save None/Null vaules to the Win object is because the company matching service
            is a learning system where there could have been a postive match previously and as the system learns
            that match may no longer be a match.
            """
            match_id = company.get('match_id')
            win_id = company.get('id')
            if win_id:
                try:
                    win = Win.objects.get(pk=win_id)
                    win.match_id = match_id
                    win.save(update_fields=['match_id'])
                    message = (
                        f'Saved match_id {match_id} to win:{win_id}' if match_id
                        else f'No match found for win:{win_id} setting to None'
                    )
                    self.stdout.write(self.style.SUCCESS(message))
                except (ObjectDoesNotExist, ValidationError):
                    self.stdout.write(
                        self.style.WARNING(f'Skipping due to an invalid ID ({win_id})')
                    )

    def handle(self, *args, **options):
        """
        Execute django managment command to import match ids from the company matching service.
        The command is timed for and could help the company matching api team with stats.
        """
        start = time.perf_counter()
        # Update the all the vaules in the database in batches
        query_set = Win.objects.all()
        p = Paginator(query_set, settings.IMPORT_MATCH_ID_TO_WIN_BATCH_SIZE)
        # Loop over the wins in batches
        for page_number in p.page_range:
            page = p.page(page_number)
            # Get the match ids from the company matching service
            json_response = self._import_match_ids(page.object_list)
            # With the reponse save the match_id against the win objects
            self._save_match_ids_to_models(json_response)

        end = time.perf_counter()

        self.stdout.write(
            self.style.SUCCESS(
                f'{query_set.count()} Wins successfully updated, completeted in {end - start:0.4f} seconds.',
            ),
        )
