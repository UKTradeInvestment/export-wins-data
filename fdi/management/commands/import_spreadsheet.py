from django.db import transaction
from django.core.management import BaseCommand
from openpyxl import load_workbook

from fdi.models import InvestmentLegacyLoad


def values(iterable):
    return [x.value for x in iterable]


class Command(BaseCommand):
    help = 'Import investment spreadsheets'

    def add_arguments(self, parser):
        parser.add_argument('files', metavar='files', nargs='+', help='One or more filenames to import.')

    def handle(self, *files, **options):
        files = options.pop('files')
        for xl_file in files:
            to_create = []
            defaults = {'filename': xl_file}
            wb = load_workbook(filename=xl_file)
            sheet = wb['Project Details']
            rows = sheet.rows
            headers = values(next(rows))

            for idx, row in enumerate(rows):
                defaults.update({'row_index': idx})
                data = dict(zip(headers, values(row)))
                if idx % 20 == 0:
                    print(f'loaded {idx}')
                to_create.append(InvestmentLegacyLoad(data=data, **defaults))
            with transaction.atomic():
                transaction.on_commit(lambda: print('transaction complete'))
                print(f'creating {len(to_create)} rows')
                InvestmentLegacyLoad.objects.bulk_create(to_create, batch_size=500)
