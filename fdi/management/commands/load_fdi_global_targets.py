from django.core.management import BaseCommand

from fdi.models import GlobalTargets
from mi.models import FinancialYear


def get_financial_year(val):
    return FinancialYear.objects.get(id=val)


class Command(BaseCommand):
    help = 'Import projects from Data Hub API'

    def add_arguments(self, parser):
        parser.add_argument(
            "year", help="<Financial Year> id", type=get_financial_year)

        parser.add_argument("--high", type=int, required=True)
        parser.add_argument("--good", type=int, required=True)
        parser.add_argument("--standard", type=int, required=True)

    def handle(self, year, high=None, good=None, standard=None, **options):
        target, created = GlobalTargets.objects.get_or_create(
            financial_year=year,
            defaults=dict(high=high, good=good, standard=standard)
        )
        if not created:
            target.high = high
            target.good = good
            target.standard = standard
            target.save()
        print(f"{'Created' if created else 'Updated'}: {target}")
