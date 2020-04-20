import logging

from celery import shared_task

from wins.company_matching_utils import (
    CompanyMatchingServiceTimeoutError,
    CompanyMatchingServiceConnectionError,
    get_match_ids,
)
from wins.models import Win


logger = logging.getLogger(__name__)


def _extract_match_id(match_json):
    """
    Extract the match_id from json response.
    {
        "matches": [
            {
                "id": "0000...",
                "match_id": 1313,
                "similarity": "001000"
            }
        ]
    }
    """
    matches = match_json.get('matches', [])
    if len(matches) == 1:
        return matches[0].get('match_id', None)
    return None


@shared_task(
    bind=True,
)
def update_match_id(self, win_id):
    """Get match id from compmay matching service and save in to the model."""
    win = Win.objects.get(pk=win_id)
    try:
        response = get_match_ids([win])
        match_id = _extract_match_id(response.json())
        win = Win.objects.get(pk=win_id)
        win.match_id = match_id
        message = (
            f'Saved match_id {match_id} to win:{win_id}' if match_id
            else f'No match found for win:{win_id} setting to None'
        )
        win.save(update_fields=['match_id'])
        logger.info(message)
    except (CompanyMatchingServiceTimeoutError, CompanyMatchingServiceConnectionError) as e:
        raise self.retry(exc=e, countdown=60)

    return win.match_id
