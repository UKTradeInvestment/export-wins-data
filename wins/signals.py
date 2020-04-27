import logging

from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save

from wins.tasks.match_id_task import update_match_id
from wins.models import Win

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Win, dispatch_uid='win_post_save_dispatch')
def save_match_id(sender, instance, **kwargs):
    """Save match id on a post save signal."""
    update_fields = kwargs.get('update_fields', [])
    """
    Ignore fixture update of if the match_id has been passed in
    update_fields e.g Win.save(update_fields=['match_id'])
    """
    if kwargs['raw'] or 'match_id' in update_fields:
        return

    transaction.on_commit(lambda: update_match_id.delay(instance.pk))
