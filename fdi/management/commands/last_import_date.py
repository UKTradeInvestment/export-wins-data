from django.core.management import BaseCommand

from fdi.models import ImportLog


class Command(BaseCommand):
    help = 'return last full import date'

    def handle(self, *args, **options):
        last_import = ImportLog.objects.last()

        if last_import:
            print(last_import.created.isoformat())
