from django.test import TestCase

from wins.models import (
    Advisor,
    Breakdown,
    CustomerResponse,
    Notification,
    Win,
)
from wins.factories import (
    AdvisorFactory,
    BreakdownFactory,
    CustomerResponseFactory,
    NotificationFactory,
    WinFactory,
)

class WinSoftDeleteTest(TestCase):

    def test_no_delete(self):
        win = WinFactory.create()
        self.assertRaises(Exception, win.delete)

    def test_real_delete(self):
        win = WinFactory.create()
        win.delete(for_real=True)
        self.assertFalse(Win.objects.including_inactive().count())

    def test_soft_delete_win(self):
        win = WinFactory.create()
        win.soft_delete()
        self.assertFalse(Win.objects.count())
        self.assertTrue(Win.objects.inactive().count())

    def test_un_soft_delete_win(self):
        win = WinFactory.create()
        win.soft_delete()
        win.un_soft_delete()
        self.assertTrue(Win.objects.count())
        self.assertFalse(Win.objects.inactive().count())

    def test_soft_delete_win_and_advisors(self):
        win = WinFactory.create()
        AdvisorFactory(win=win)
        win.soft_delete()
        self.assertFalse(Win.objects.count())
        self.assertTrue(Win.objects.inactive().count())
        self.assertFalse(Advisor.objects.count())
        self.assertTrue(Advisor.objects.inactive().count())

    def test_un_soft_delete_win_and_advisors(self):
        win = WinFactory.create()
        AdvisorFactory(win=win)
        win.soft_delete()
        win.un_soft_delete()
        self.assertTrue(Win.objects.count())
        self.assertFalse(Win.objects.inactive().count())
        self.assertTrue(Advisor.objects.count())
        self.assertFalse(Advisor.objects.inactive().count())

    def test_soft_delete_win_and_breakdowns(self):
        win = WinFactory.create()
        BreakdownFactory(win=win)
        win.soft_delete()
        self.assertFalse(Win.objects.count())
        self.assertTrue(Win.objects.inactive().count())
        self.assertFalse(Breakdown.objects.count())
        self.assertTrue(Breakdown.objects.inactive().count())

    def test_soft_delete_win_and_notifications(self):
        win = WinFactory.create()
        NotificationFactory(win=win)
        win.soft_delete()
        self.assertFalse(Win.objects.count())
        self.assertTrue(Win.objects.inactive().count())
        self.assertFalse(Notification.objects.count())
        self.assertTrue(Notification.objects.inactive().count())

    def test_soft_delete_win_and_responses(self):
        win = WinFactory.create()
        CustomerResponseFactory(win=win)
        win.soft_delete()
        self.assertFalse(Win.objects.count())
        self.assertTrue(Win.objects.inactive().count())
        self.assertFalse(CustomerResponse.objects.count())
        self.assertTrue(CustomerResponse.objects.inactive().count())

    def test_un_soft_delete_win_and_responses(self):
        win = WinFactory.create()
        CustomerResponseFactory(win=win)
        win.soft_delete()
        win.un_soft_delete()
        self.assertTrue(Win.objects.count())
        self.assertFalse(Win.objects.inactive().count())
        self.assertTrue(CustomerResponse.objects.count())
        self.assertFalse(CustomerResponse.objects.inactive().count())
