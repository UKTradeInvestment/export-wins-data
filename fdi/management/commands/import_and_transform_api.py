from datetime import datetime, timedelta

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = 'Import projects from Data Hub API and transform using exisiting commands'

    def handle(self, *args, **options):
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday.strftime('--startdate=%Y-%m-%dT00:00:00')
        call_command('import_api', start_date)
        call_command('transform_api')
