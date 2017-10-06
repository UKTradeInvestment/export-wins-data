from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter
from itertools import groupby
from operator import attrgetter, itemgetter

from django.db.models import Count, Sum, Q, OuterRef, Subquery
from django.utils import timezone

from django_countries.fields import Country as DjangoCountry
from pytz import UTC
from core.views import BaseMIView
from mi.models import (
    Sector
)
from mi.utils import (
    average,
    percentage,
    percentage_formatted,
    months_between,
    month_iterator,
)
from wins.models import Notification, Win, _get_open_hvcs, HVC


class BaseExportMIView(BaseMIView):
    """ Base view for other MI endpoints to inherit from """

    def _hvc_overview(self, targets):
        """ Make an overview dict for a list of targets """

        return {
            'target': sum(t.target for t in targets),
            'campaigns': sorted([t.name for t in targets]),
        }

    def _win_date_for_grouping(self, win):
        if hasattr(win, 'confirmation'):
            return win['confirmation__created'].date()
        else:
            return win['date']


class BaseWinMIView(BaseExportMIView):
    """ Base view with Win-related MI helpers """

    # cumulative values for `_breakdowns_cumulative` method
    hvc_confirm_cu_number = hvc_confirm_cu_value = hvc_non_cu_number = hvc_non_cu_value = 0
    non_hvc_confirm_cu_number = non_hvc_confirm_cu_value = non_hvc_non_cu_number = non_hvc_non_cu_value = 0
    non_export_confirm_cu_number = non_export_confirm_cu_value = non_export_non_cu_number = non_export_non_cu_value = 0
    start_of_2017_fy = datetime(
        year=2017,
        month=4,
        day=1,
        tzinfo=timezone.utc,
    )

    def _wins_filter(self):
        """
        Commonalities of generic wins functions are extracted into this filter
        function.
        :return: A wins QuerySet for the financial year and unconfjrmed wins
        """
        # get Wins where the customer responded in the given FY
        win_filter = Q(confirmation__created__range=(
            self._date_range_start(),
            self._date_range_end()
        ))

        # if we're in the current FY, also include unconfirmed Wins
        # these wins are now limited for past 12 months
        if self.fin_year.is_current:
            unconfirmed_cutoff = datetime.utcnow() - relativedelta(years=1)
            win_filter = win_filter | Q(
                date__gte=unconfirmed_cutoff,
                confirmation__isnull=True,
            )

        return win_filter

    def _wins(self, filter=None):
        """ Return queryset of Wins used by all Endpoints

        All endpoints should derive their Wins from this single source of
        truth.

        See `_win_status` for specifics of how these Wins are used.

        Note that we could filter Wins that the customer has responded to
        here in order to exclude rejected Wins for 2017/18, but choose to do
        it in `_win_status` so that we can later include data on rejected
        Wins.

        """
        fields = [
            "id",
            'hvc',
            'sector',
            'date',
            'total_expected_export_value',
            'total_expected_non_export_value',
            'confirmation__created',
            'confirmation__agree_with_win',
            'company_name',
            'cdms_reference',
            'lead_officer_name',
            'location',
            'export_experience'
        ]
        newest_notification = Notification.objects.filter(win=OuterRef(
            'pk'), type=Notification.TYPE_CUSTOMER).order_by('-created')

        wins = None
        if not filter:
            wins = Win.objects.filter(self._wins_filter()).only(*fields).values(*fields).annotate(
                notifications__created=Subquery(newest_notification.values('created')[:1]))
        else:
            wins = Win.objects.filter(filter).only(*fields).values(*fields).annotate(
                notifications__created=Subquery(newest_notification.values('created')[:1]))
        return wins

    def _non_hvc_wins(self):
        return self._wins().non_hvc(fin_year=self.fin_year)

    def _hvc_wins(self):
        return self._wins().hvc(fin_year=self.fin_year)

    def _win_status(self, win):
        """ Determine if Win is confirmed, unconfirmed or rejected

        If Win has had notification sent, but no response, it is unconfirmed
        and belongs in current FY, since confirmation can only happen in
        current FY.

        Note wins can only be unconfirmed in current FY, since they can only
        be confirmed in current FY.

        If Win is in 2016/17 FY, it is confirmed if the customer has
        responded, while if it is in subsequent FY it is confirmed only if
        customer has explicitly agreed, else it is rejected.
        """

        if not win['confirmation__created']:
            return 'unconfirmed'

        if win['confirmation__created'] < self.start_of_2017_fy:
            return 'confirmed'
        else:
            if win['confirmation__agree_with_win']:
                return 'confirmed'
            else:
                return 'rejected'

    def _colours(self, hvc_wins, targets):
        """ Determine colour of all HVCs based on progress toward target

        Return a dict of status colour counts e.g.
        {'red': 3, 'amber': 2, 'green': 4, 'zero': 2}

        """

        # initialize with default
        colours = {
            'red': 0,
            'amber': 0,
            'green': 0,
            'zero': 0,
        }

        hvc_colours = []
        for t in targets:
            target_wins = [win for win in hvc_wins if win['hvc']
                           [:-2] == t.charcode[:-2]]
            current_val, _ = self._confirmed_unconfirmed(target_wins)
            hvc_colours.append(self._get_status_colour(t.target, current_val))

        colours.update(dict(Counter(hvc_colours)))
        return colours

    def _average_confirm_time(self, **win_filter):
        """ Average confirmation time of Wins matching given filter """

        # fetch all notifications with response date, ordered by win id and
        # notification creation date, so that it is easy to group
        # notifications by win and then find each win's earliest notification
        notifications = Notification.objects.filter(
            type__exact='c',
            win__confirmation__isnull=False,
            **win_filter
        ).values(
            'win__id',
            'created',
            'win__confirmation__created',
        ).order_by(
            'win__id',
            'created'
        )
        confirm_times = []
        for win_id, values_grouper in groupby(notifications, itemgetter('win__id')):
            earliest_values = next(iter(values_grouper))
            from_date = earliest_values['win__confirmation__created']
            to_date = earliest_values['created']
            delta = from_date.date() - to_date.date()
            confirm_times.append(delta.days)

        avg_confirm_time = average(confirm_times)
        return avg_confirm_time or 0.0

    def _average_confirm_time_for_wins(self, wins):
        confirm_times = []
        for win in wins:
            if self._win_status(win) == "confirmed":
                from_date = win['confirmation__created']
                to_date = win['notifications__created']
                if from_date and to_date:
                    delta = from_date.date() - to_date.date()
                    confirm_times.append(delta.days)

        avg_confirm_time = average(confirm_times)

        return avg_confirm_time or 0.0

    def _overview_target_percentage(self, wins, total_target):
        """ Percentages of confirmed/unconfirmed wins against total target """

        confirmed, unconfirmed = self._confirmed_unconfirmed(wins)
        confirmed = percentage_formatted(confirmed, total_target)
        unconfirmed = percentage_formatted(unconfirmed, total_target)
        return {
            'confirmed': confirmed,
            'unconfirmed': unconfirmed,
        }

    def _overview_win_percentages(self, hvc_wins, non_hvc_wins):
        """ Percentages of total confirmed/unconfirmed value HVC & non-HVC """

        hvc_confirmed, hvc_unconfirmed = self._confirmed_unconfirmed(hvc_wins)
        non_hvc_confirmed, non_hvc_unconfirmed = self._confirmed_unconfirmed(
            non_hvc_wins)

        total_confirmed = hvc_confirmed + non_hvc_confirmed
        total_unconfirmed = hvc_unconfirmed + non_hvc_unconfirmed
        total_win_percent = {
            'hvc': {
                'confirmed': 0,
                'unconfirmed': 0
            },
            'non_hvc': {
                'confirmed': 0,
                'unconfirmed': 0
            }
        }
        if total_confirmed != 0:
            total_win_percent['hvc']['confirmed'] = percentage(
                hvc_confirmed, total_confirmed)
            total_win_percent['non_hvc']['confirmed'] = percentage(
                non_hvc_confirmed, total_confirmed)

        if total_unconfirmed != 0:
            total_win_percent['hvc']['unconfirmed'] = percentage(
                hvc_unconfirmed, total_unconfirmed)
            total_win_percent['non_hvc']['unconfirmed'] = percentage(
                non_hvc_unconfirmed, total_unconfirmed)

        return total_win_percent

    def _days_into_year(self):
        """
        abstract away identifying number of days we are into the financial year.

        Return usual number of days, if we are dealing with current financial year

        If in case of previous ones, just return 365
        """

        days_into_year = (datetime.today().replace(
            tzinfo=UTC) - self.fin_year.start).days

        if days_into_year > 365:
            return 365

        return days_into_year

    def _get_status_colour(self, target, current_value):
        """
        Algorithm to determine HVC performance status colour

        `run_rate` is percentage of value achieved out of `target as of today` i.e. prorated target

        zero: for 0 target campaigns
        green: when run_rate > 45%
        red: when run_rate < 25%
        amber: rest of them
        """

        if target == 0:
            return 'zero'

        # calculate prorated target based on number of days
        prorated_target = (target / 365) * self._days_into_year()
        run_rate = (current_value * 100) / prorated_target

        if run_rate > 45:
            return 'green'

        if run_rate < 25:
            return 'red'

        return 'amber'

    def _breakdown_wins(self, wins, non_export=False):
        """
        Breakdown Wins by confirmed and non-confirmed
        Clarification on not including non-export for non-HVC wins:
        Non-export value is the value of a win entered into the export win system that is not technically an export
        by definitions of export e.g. when we lobby a government to reduce corporate taxes – that profit back to
        the UK is a benefit to us but not an export. It has nothing to do with Non-HVC wins which are export wins,
        which could contain 0 or lots of non-export value as with any export win, but do not fall within a HVC.
        """

        confirmed = []
        unconfirmed = []

        for win in wins:
            if non_export:
                value = win['total_expected_non_export_value']
            else:
                value = win['total_expected_export_value']

            win_status = self._win_status(win)
            if win_status == 'confirmed':
                confirmed.append(value)
            elif win_status == 'unconfirmed':
                unconfirmed.append(value)
            elif win_status == 'rejected':
                pass  # todo

        return {
            'value': {
                'confirmed': sum(confirmed),
                'unconfirmed': sum(unconfirmed),
                'total': sum(confirmed) + sum(unconfirmed),
            },
            'number': {
                'confirmed': len(confirmed),
                'unconfirmed': len(unconfirmed),
                'total': len(confirmed) + len(unconfirmed),
            },

        }

    def _breakdowns(self, hvc_wins, non_hvc_wins=None, include_non_hvc=True):
        """ Get breakdown of data for wins

        Result looks like:
        {
            'export': {
                'hvc': {
                    'value': ...,
                    'number': ...,
                },
                'non_hvc' <optional>:{
                   'value': ...,
                   'number': ...,
                }
            },
            'non_export': {
               'value': ...,
               'number': ...,
            }

        }

        """
        result = {
            'export': {
                'hvc': self._breakdown_wins(hvc_wins),
            },
            'non_export': self._breakdown_wins(hvc_wins, non_export=True),
        }

        confirmed_value = result['export']['hvc']['value']['confirmed']
        unconfirmed_value = result['export']['hvc']['value']['unconfirmed']
        confirmed_number = result['export']['hvc']['number']['confirmed']
        unconfirmed_number = result['export']['hvc']['number']['unconfirmed']

        if include_non_hvc:
            result['export']['non_hvc'] = self._breakdown_wins(non_hvc_wins)

            confirmed_value += result['export']['non_hvc']['value']['confirmed']
            unconfirmed_value += result['export']['non_hvc']['value']['unconfirmed']
            confirmed_number += result['export']['non_hvc']['number']['confirmed']
            unconfirmed_number += result['export']['non_hvc']['number']['unconfirmed']

        result['export']['totals'] = {
            'value': {
                'confirmed': confirmed_value,
                'unconfirmed': unconfirmed_value,
                'grand_total': confirmed_value + unconfirmed_value,
            },
            'number': {
                'confirmed': confirmed_number,
                'unconfirmed': unconfirmed_number,
                'grand_total': confirmed_number + unconfirmed_number,
            }
        }

        return result

    def _progress_breakdown(self, wins, target):
        """ Breakdown wins by progress toward HVC target """

        breakdown = self._breakdown_wins(wins)
        confirmed_percent = percentage_formatted(
            breakdown['value']['confirmed'], target)
        unconfirmed_percent = percentage_formatted(
            breakdown['value']['unconfirmed'], target)
        return {
            'hvc': breakdown,
            'target': target,
            'change': 'up',
            'progress': {
                'confirmed_percent': confirmed_percent,
                'unconfirmed_percent': unconfirmed_percent,
                'status': self._get_status_colour(target, breakdown['value']['confirmed'])
            },
        }

    def _breakdowns_cumulative(self, wins, include_non_hvc=True):
        """ Breakdown wins by HVC, confirmed and non-export - cumulative

        Month-by-month breakdown using class values

        """
        hvc_confirmed = []
        hvc_unconfirmed = []
        non_hvc_confirmed = []
        non_hvc_unconfirmed = []
        non_export_confirmed = []
        non_export_unconfirmed = []
        open_hvcs = set(_get_open_hvcs(self.fin_year))

        for win in wins:
            export_value = win['total_expected_export_value']
            win_status = self._win_status(win)
            if win['hvc'] and win['hvc'][:-2] in open_hvcs:
                if win_status == 'confirmed':
                    hvc_confirmed.append(export_value)
                elif win_status == 'unconfirmed':
                    hvc_unconfirmed.append(export_value)
                elif win_status == 'rejected':
                    pass  # todo
            else:
                if win_status == 'confirmed':
                    non_hvc_confirmed.append(export_value)
                elif win_status == 'unconfirmed':
                    non_hvc_unconfirmed.append(export_value)
                elif win_status == 'rejected':
                    pass  # todo

            non_export_value = win['total_expected_non_export_value']
            if win_status == 'confirmed':
                non_export_confirmed.append(non_export_value)
            elif win_status == 'unconfirmed':
                non_export_unconfirmed.append(non_export_value)
            elif win_status == 'rejected':
                pass  # todo

        # these store cumulative values of each month (see class definition)
        self.hvc_confirm_cu_number += len(hvc_confirmed)
        self.hvc_non_cu_number += len(hvc_unconfirmed)
        self.hvc_confirm_cu_value += sum(hvc_confirmed)
        self.hvc_non_cu_value += sum(hvc_unconfirmed)
        self.non_hvc_confirm_cu_number += len(non_hvc_confirmed)
        self.non_hvc_non_cu_number += len(non_hvc_unconfirmed)
        self.non_hvc_confirm_cu_value += sum(non_hvc_confirmed)
        self.non_hvc_non_cu_value += sum(non_hvc_unconfirmed)
        self.non_export_confirm_cu_number += len(non_export_confirmed)
        self.non_export_non_cu_number += len(non_export_unconfirmed)
        self.non_export_confirm_cu_value += sum(non_export_confirmed)
        self.non_export_non_cu_value += sum(non_export_unconfirmed)

        total_hvc_value = self.hvc_confirm_cu_value + self.hvc_non_cu_value
        total_non_hvc_value = self.non_hvc_confirm_cu_value + self.non_hvc_non_cu_value
        total_confirm_value = self.hvc_confirm_cu_value + self.non_hvc_confirm_cu_value
        total_non_conf_value = self.hvc_non_cu_value + self.non_hvc_non_cu_value

        total_hvc_number = self.hvc_confirm_cu_number + self.hvc_non_cu_number
        total_non_hvc_number = self.non_hvc_confirm_cu_number + self.non_hvc_non_cu_number
        total_confirm_number = self.hvc_confirm_cu_number + self.non_hvc_confirm_cu_number
        total_non_conf_number = self.hvc_non_cu_number + self.non_hvc_non_cu_number

        result = {
            'export': {
                'hvc': {
                    'value': {
                        'confirmed': self.hvc_confirm_cu_value,
                        'unconfirmed': self.hvc_non_cu_value,
                        'total': total_hvc_value,
                    },
                    'number': {
                        'confirmed': self.hvc_confirm_cu_number,
                        'unconfirmed': self.hvc_non_cu_number,
                        'total': total_hvc_number,
                    },
                },
            },
            'non_export': {
                'value': {
                    'confirmed': self.non_export_confirm_cu_value,
                    'unconfirmed': self.non_export_non_cu_value,
                    'total': (self.non_export_confirm_cu_value + self.non_export_non_cu_value),
                },
                'number': {
                    'confirmed': self.non_export_confirm_cu_number,
                    'unconfirmed': self.non_export_non_cu_number,
                    'total': (self.non_export_confirm_cu_number + self.non_export_non_cu_number),
                }
            }
        }

        if include_non_hvc:
            result['export']['non_hvc'] = {
                'value': {
                    'confirmed': self.non_hvc_confirm_cu_value,
                    'unconfirmed': self.non_hvc_non_cu_value,
                    'total': total_non_hvc_value,
                },
                'number': {
                    'confirmed': self.non_hvc_confirm_cu_number,
                    'unconfirmed': self.non_hvc_non_cu_number,
                    'total': total_non_hvc_number,
                }
            }

        result['export']['totals'] = {
            'value': {
                'confirmed': total_confirm_value if include_non_hvc else self.hvc_confirm_cu_value,
                'unconfirmed': total_non_conf_value if include_non_hvc else self.hvc_non_cu_value,
                'grand_total': total_hvc_value + total_non_hvc_value if include_non_hvc else total_hvc_value,
            },
            'number': {
                'confirmed': total_confirm_number if include_non_hvc else self.hvc_confirm_cu_number,
                'unconfirmed': total_non_conf_number if include_non_hvc else self.hvc_non_cu_number,
                'grand_total': total_hvc_number + total_non_hvc_number if include_non_hvc else total_hvc_number,
            },
        }
        return result

    def _group_wins_by_target(self, wins, targets):
        """ Take wins and targets, return list of [(target, target_wins)] """

        # convenient for testing to be ordered by campaign_id
        targets = sorted(targets, key=attrgetter('campaign_id'))

        def target_wins(target):
            return [w for w in wins if w['hvc'][:-2] == target.campaign_id]

        return [(t, target_wins(t)) for t in targets]

    def _confirmed_unconfirmed(self, wins):
        """ Find total Confirmed & Unconfirmed export value for given Wins """

        confirmed = sum(w['total_expected_export_value']
                        for w in wins if self._win_status(w) == 'confirmed')
        unconfirmed = sum(w['total_expected_export_value']
                          for w in wins if self._win_status(w) == 'unconfirmed')
        return confirmed, unconfirmed

    def _top_non_hvc(self, non_hvc_wins_qs, records_to_retrieve=5):
        """ Get dict of data about non-HVC wins

        percentComplete is based on the top value being 100%
        averageWinValue is total non_hvc win value for the sector/total number of wins during the financial year
        averageWinPercent is therefore averageWinValue * 100/Total win value for the sector/market

        """
        non_hvc_wins = non_hvc_wins_qs.values(
            'country',
            'sector'
        ).annotate(
            total_value=Sum('total_expected_export_value'),
            total_wins=Count('id')
        ).order_by('-total_value')[:records_to_retrieve]

        # make a lookup to get names efficiently
        sector_id_to_name = {s.id: s.name for s in Sector.objects.all()}
        top_value = int(non_hvc_wins[0]['total_value']
                        ) if non_hvc_wins else None
        return [
            {
                'region': DjangoCountry(w['country']).name,
                'sector': sector_id_to_name[w['sector']],
                'totalValue': w['total_value'],
                'totalWins': w['total_wins'],
                'percentComplete': int(percentage(w['total_value'], top_value)),
                'averageWinValue': int(w['total_value'] / w['total_wins']),
                'averageWinPercent': int(percentage((w['total_value'] / w['total_wins']), top_value)),
            }
            for w in non_hvc_wins
        ]

    def _win_table_wins(self, hvc_wins, non_hvc_wins=None):
        all_hvcs = {"{}{}".format(x["campaign_id"], x["financial_year"]): x["name"]
                    for x in HVC.objects.all().values("campaign_id", "financial_year", "name")}

        def confirmed_date(win):
            if win["confirmation__created"]:
                return win["confirmation__created"]

            return None

        def status(win):
            if not win["notifications__created"]:
                return "email_not_sent"
            elif not win["confirmation__created"]:
                return "response_not_received"
            elif win["confirmation__agree_with_win"]:
                return "customer_confirmed"
            else:
                return "customer_rejected"

        def credit(win):
            return self._win_status(win) == "confirmed"

        results = {
            "hvc": [
                {
                    "id": win["id"],
                    "hvc": {
                        "code": win["hvc"][:4],
                        "name": all_hvcs[win["hvc"]]
                    },
                    "company": {
                        "name": win["company_name"],
                        "cdms_id": win["cdms_reference"]
                    },
                    "lead_officer": {
                        "name": win["lead_officer_name"],
                    },
                    "credit": credit(win),
                    "win_date": confirmed_date(win),
                    "export_amount": win["total_expected_export_value"],
                    "status": status(win)
                }
                for win in hvc_wins
            ],
        }
        if non_hvc_wins:
            results["non_hvc"] = [
                {
                    "id": win["id"],
                    "company": {
                        "name": win["company_name"],
                        "cdms_id": win["cdms_reference"]
                    },
                    "lead_officer": {
                        "name": win["lead_officer_name"],
                    },
                    "credit": credit(win),
                    "win_date": confirmed_date(win),
                    "export_amount": win["total_expected_export_value"],
                    "status": status(win)
                }
                for win in non_hvc_wins
            ]

        return results

    def _month_breakdowns(self, wins, include_non_hvc=True):
        """ generic internal that groups wins into monthly aggregation """
        month_to_wins = self._group_wins_by_month(wins)
        return [
            {
                'date': date_str,
                'totals': self._breakdowns_cumulative(month_wins, include_non_hvc),
            }
            for date_str, month_wins in month_to_wins
        ]

    def _group_wins_by_month(self, wins):
        """ generic internal that groups wins into monthly aggregation """
        sorted_wins = sorted(wins, key=self._win_date_for_grouping)
        month_grouping = []
        start_date = self._date_range_start()
        end_date = self._date_range_end()
        # group wins by date (month-year)
        for k, g in groupby(sorted_wins, key=self._win_date_for_grouping):
            month_wins = list(g)
            date_str = month_wins[0]['date'].strftime('%Y-%m')
            month_grouping.append((date_str, month_wins))

        # Add missing months within the financial year until current month
        months_range = []
        for item in month_iterator(start_date, end_date):
            date_str = '{:d}-{:02d}'.format(*item)
            months_range.append(date_str)
            existing = [m for m in month_grouping if m[0] == date_str]
            if len(existing) == 0:
                month_grouping.append((date_str, list()))

        sorted_month_grouping = sorted(month_grouping, key=lambda tup: tup[0])
        # return only months between date range, FY by default
        return [wins for wins in sorted_month_grouping if wins[0] in months_range]
