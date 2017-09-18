import os
from django.db import transaction
from django.core.management import BaseCommand
from openpyxl import load_workbook

from fdi.models import InvestmentLegacyLoad, CompanyLegacyLoad


def values(iterable):
    return [x.value for x in iterable]


def rows_to_investment(rows, filename):
    headers = values(next(rows))
    for idx, row in enumerate(rows):
        data = dict(zip(headers, values(row)))
        if idx % 200 == 0:
            print(f'inv: loaded {idx}')
        yield InvestmentLegacyLoad(data=data, row_index=idx, filename=os.path.basename(filename))


def rows_to_company(rows, filename):
    headers = values(next(rows))
    for idx, row in enumerate(rows):
        data = dict(zip(headers, values(row)))
        if idx % 200 == 0:
            print(f'company: loaded {idx}')
        yield CompanyLegacyLoad(data=data, row_index=idx, filename=os.path.basename(filename))


def file_to_rows(xl_file, sheet):
    wb = load_workbook(filename=xl_file)
    sheet_projects = wb[sheet]
    rows = sheet_projects.rows
    return rows


def process_file(xl_file):
    investment_rows = file_to_rows(xl_file, 'Project Details')
    org_rows = file_to_rows(xl_file, 'Organisation Details')
    return list(rows_to_investment(investment_rows, xl_file)), list(rows_to_company(org_rows, xl_file))


def process_files(files):
    to_create = []
    for xl_file in files:
        to_create.append(process_file(xl_file))

    with transaction.atomic():
        for t in to_create:
            bulk_create(*t)


def bulk_create(projects_to_create, orgs_to_create):
    with transaction.atomic():
        transaction.on_commit(lambda: print('transaction complete'))
        print(f'creating {len(projects_to_create)} rows')
        InvestmentLegacyLoad.objects.bulk_create(projects_to_create, batch_size=500)
        CompanyLegacyLoad.objects.bulk_create(orgs_to_create, batch_size=500)


def run(files):
    process_files(files)


class Command(BaseCommand):
    """
    called like this:
    ./manage.py load_spreadsheets ~/Downloads/Investment2014.xlsx, ~/Downloads/Investment2015.xlsx
    """

    help = 'Import investment spreadsheets'

    def add_arguments(self, parser):
        parser.add_argument('files', metavar='files', nargs='+', help='One or more filenames to import.')

    def handle(self, *files, **options):
        files = options.pop('files')
        run(files)
