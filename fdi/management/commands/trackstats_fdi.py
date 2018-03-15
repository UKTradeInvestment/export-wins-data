from django.core.management import BaseCommand
from trackstats.models import StatisticByDateAndObject, Metric, Period

from fdi.models import Investments, FinancialYear


class Command(BaseCommand):
    """
    called like this:
    ./manage.py trackstats_fdi

    Freezes the stats like number of wins into the database using the `trackstats`
    """

    help = 'Freeze stats for FDI'

    def handle(self, *args, **options):

        fy = FinancialYear.objects.get(pk=FinancialYear.current_fy())
        qs = Investments.objects.involved().for_year(fy)
        total_count = qs.count()

        # record total number of investments
        rec = StatisticByDateAndObject.objects.record(
            metric=Metric.objects.INVESTMENT_COUNT,
            period=Period.LIFETIME,
            object=fy,
            value=total_count
        )
        print(rec)

        won_count = qs.won().count()
        rec = StatisticByDateAndObject.objects.record(
            metric=Metric.objects.INVESTMENT_WON_COUNT,
            period=Period.LIFETIME,
            object=fy,
            value=won_count
        )
        print(rec)

        verify_win_count = qs.verified().count()
        rec = StatisticByDateAndObject.objects.record(
            metric=Metric.objects.INVESTMENT_VERIFY_WIN_COUNT,
            period=Period.LIFETIME,
            object=fy,
            value=verify_win_count
        )
        print(rec)

        active_count = qs.active().count()
        rec = StatisticByDateAndObject.objects.record(
            metric=Metric.objects.INVESTMENT_ACTIVE_COUNT,
            period=Period.LIFETIME,
            object=fy,
            value=active_count
        )
        print(rec)

        pipeline_count = qs.pipeline().count()
        rec = StatisticByDateAndObject.objects.record(
            metric=Metric.objects.INVESTMENT_PIPELINE_COUNT,
            period=Period.LIFETIME,
            object=fy,
            value=pipeline_count
        )
        print(rec)
