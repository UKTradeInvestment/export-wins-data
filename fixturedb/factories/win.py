from datetime import timedelta
import django.utils.datetime_safe as datetime
from django.utils.timezone import get_current_timezone
from factory.fuzzy import FuzzyChoice

from wins.constants import SECTORS
from wins.factories import WinFactory, NotificationFactory, CustomerResponseFactory
from wins.models import Notification


def create_win_factory(user, sector_choices=None, default_date=None):
    if not default_date:
        default_date = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())

    if not sector_choices:
        sector_choices = dict(SECTORS).keys()

    def inner(hvc_code, sector_id=None, win_date=None, export_value=None,
              confirm=False, notify_date=None, response_date=None, country=None,
              fin_year=2016, agree_with_win=True):
        """ generic function creating `Win` """
        if not sector_id:
            sector_id = FuzzyChoice(sector_choices)

        if not win_date:
            win_date = default_date

        if hvc_code is not None:
            win = WinFactory(user=user, hvc=hvc_code + str(fin_year)[-2:], sector=sector_id, date=win_date)
        else:
            win = WinFactory(user=user, sector=sector_id, date=win_date)
        win.save()

        if country is not None:
            win.country = country
            win.save()

        if export_value is not None:
            win.total_expected_export_value = export_value
            win.save()

        if confirm:
            if not notify_date:
                notify_date = win_date + timedelta(days=1)
            notification = NotificationFactory(win=win)
            notification.type = Notification.TYPE_CUSTOMER
            notification.created = notify_date
            notification.save()
            if not response_date:
                response_date = notify_date + timedelta(days=1)
            response = CustomerResponseFactory(win=win, agree_with_win=agree_with_win)
            response.created = response_date
            response.save()
        return win

    inner.sector_choices = sector_choices
    return inner
