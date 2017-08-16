from datetime import timedelta
import django.utils.datetime_safe as datetime
from django.utils.timezone import get_current_timezone
from factory.fuzzy import FuzzyChoice

from wins.constants import SECTORS, HQ_TEAM_REGION_OR_POST
from wins.factories import WinFactory, NotificationFactory, CustomerResponseFactory
from wins.models import Notification


def create_win_factory(user, sector_choices=None, default_date=None, default_team_type=None, default_hq_team=None):
    if not default_date:
        default_date = datetime.datetime(2016, 5, 25, tzinfo=get_current_timezone())

    if not sector_choices:
        sector_choices = dict(SECTORS).keys()

    def inner(hvc_code, sector_id=None, win_date=None, export_value=None,
              confirm=False, notify_date=None, response_date=None, country=None,
              fin_year=2016, agree_with_win=True, team_type=None, hq_team=None):
        """ generic function creating `Win` """
        if not sector_id:
            sector_id = FuzzyChoice(sector_choices)

        if not win_date:
            win_date = default_date

        if not team_type:
            team_type = default_team_type

        if not hq_team:
            hq_team = default_hq_team

        if team_type and not hq_team:
            hq_team = FuzzyChoice([id for id, name in HQ_TEAM_REGION_OR_POST if id.startswith(team_type)])

        if hvc_code is not None:
            win = WinFactory(
                user=user,
                hvc=hvc_code + str(fin_year)[-2:],
                sector=sector_id,
                date=win_date,
            )
        else:
            win = WinFactory(
                user=user,
                sector=sector_id,
                date=win_date,
            )
        win.save()

        if country is not None:
            win.country = country
            win.save()

        if export_value is not None:
            win.total_expected_export_value = export_value
            win.save()

        if team_type is not None:
            win.team_type = team_type
            win.hq_team = hq_team
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
