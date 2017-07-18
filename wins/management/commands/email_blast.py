import datetime

from django.core.management.base import BaseCommand
from django.db.models import Count

from wins.models import Notification, Win
from wins.notifications import send_customer_email


class Command(BaseCommand):

    def handle(self, *args, **options):
        """ Send customer email reminder to all applicable customers

        - have had at least one email
        - last reminded a while ago
        - haven't completed response form

        """
        time_ago = datetime.date.today() - datetime.timedelta(days=7)
        to_remind_wins = Win.objects.filter(
            confirmation__isnull=True,
            complete=True,
        ).exclude(
            notifications__type='c',
            notifications__created__gt=time_ago,
        )

        to_remind_wins = Win.objects.filter(
            confirmation__isnull=True,
            complete=True,).exclude(
            notifications__type='c',
            notifications__created__gt=time_ago,).annotate(
            customer_notifications=Count('notifications')).exclude(
            customer_notifications__gt=4)


        for win in to_remind_wins:
            send_customer_email(win)
            notification = Notification(
                win=win,
                user=win.user,
                recipient=win.customer_email_address,
                type=Notification.TYPE_CUSTOMER,
            )
            notification.save()
