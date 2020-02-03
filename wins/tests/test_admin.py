from unittest.mock import MagicMock

from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.utils.timezone import now

from users.factories import UserFactory
from wins.admin import BREAKDOWN_TYPE_TO_NAME, WinAdmin
from wins.constants import BREAKDOWN_TYPES
from wins.models import Breakdown, Win


class WinAdminTestCase(TestCase):
    def test_save_model(self):
        now_ = now()
        win = Win.objects.create(customer_location=1, date=now_, total_expected_export_value=0,
                                 goods_vs_services=1, total_expected_non_export_value=0, sector=1,
                                 type_of_support_1=1, is_personally_confirmed=True,
                                 is_line_manager_confirmed=False, user=UserFactory(),
                                 complete=False, total_expected_odi_value=0)
        for i, t in BREAKDOWN_TYPES:
            assert getattr(win, f'total_expected_{BREAKDOWN_TYPE_TO_NAME[t]}_value') == 0
            Breakdown.objects.create(win=win, type=i, value=i, year=now_.year)
        WinAdmin(model=Win, admin_site=AdminSite()).save_related(
            request=None, form=MagicMock(), formsets=[MagicMock(queryset=[MagicMock(win=win)])],
            change=None)
        win.refresh_from_db()
        for i, t in BREAKDOWN_TYPES:
            assert getattr(win, f'total_expected_{BREAKDOWN_TYPE_TO_NAME[t]}_value') == i
