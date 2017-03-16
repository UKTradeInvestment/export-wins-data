from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import Win


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--ids", type=str)

    def handle(self, *args, **options):

        win_ids = [wid.replace('-', '') for wid in options['ids'].split(',')]
        for win_id in win_ids:
            try:
                win = Win.objects.get(id=win_id)
            except Win.DoesNotExist:
                print('no such win')
            else:
                print(
                    'win.id', win.id,
                    'win.customer_email_address', win.customer_email_address,
                    'win.customer_name', win.customer_name
                )
