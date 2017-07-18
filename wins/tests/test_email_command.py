import datetime

from django.core.management import call_command
from django.test import TestCase

from wins.factories import WinFactory
from wins.models import Win, Notification


class CommandsTestCase(TestCase):
    def _call_command(self):
        args = []
        opts = {}
        call_command('email_blast', *args, **opts)

    def test_no_wins(self):
        self._call_command()

    def test_new_win(self):
        WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=datetime.datetime.now(),
            complete=True,
        )
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 1)

    def test_win_older_than_7_days(self):
        old_date = datetime.date.today() - datetime.timedelta(days=8)
        WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=old_date,
            complete=True,
        )
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 0)

    def test_win_border_check_7_days(self):
        old_date = datetime.date.today() - datetime.timedelta(days=7)
        WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=old_date,
            complete=True,
        )
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 1)

    def test_win_with_1_notifications(self):
        old_date = datetime.date.today() - datetime.timedelta(days=6)
        win = WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=old_date,
            complete=True,
        )
        notification = Notification(
            win=win,
            user=win.user,
            recipient=win.customer_email_address,
            type=Notification.TYPE_CUSTOMER,
        )
        notification.save()
        self.assertTrue(win.notifications.count(), 1)
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 2)

    def test_win_with_2_notifications(self):
        old_date = datetime.date.today() - datetime.timedelta(days=6)
        win = WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=old_date,
            complete=True,
        )
        for _ in range(1):
            notification = Notification(
                win=win,
                user=win.user,
                recipient=win.customer_email_address,
                type=Notification.TYPE_CUSTOMER,
            )
            notification.save()
        self.assertTrue(win.notifications.count(), 2)
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 3)

    def test_win_with_3_notifications(self):
        old_date = datetime.date.today() - datetime.timedelta(days=6)
        win = WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=old_date,
            complete=True,
        )
        for _ in range(2):
            notification = Notification(
                win=win,
                user=win.user,
                recipient=win.customer_email_address,
                type=Notification.TYPE_CUSTOMER,
            )
            notification.save()
        self.assertTrue(win.notifications.count(), 3)
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 4)

    def test_win_with_4_notifications_no_more_email(self):
        old_date = datetime.date.today() - datetime.timedelta(days=6)
        win = WinFactory(
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            date=old_date,
            complete=True,
        )
        for _ in range(3):
            notification = Notification(
                win=win,
                user=win.user,
                recipient=win.customer_email_address,
                type=Notification.TYPE_CUSTOMER,
            )
            notification.save()
        self.assertTrue(win.notifications.count(), 4)
        self._call_command()
        win = Win.objects.get(id='6e18a056-1a25-46ce-a4bb-0553a912706d')
        self.assertTrue(win.notifications.count(), 4)
