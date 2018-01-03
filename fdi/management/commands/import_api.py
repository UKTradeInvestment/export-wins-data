import argparse
import json
import requests
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.core.management import BaseCommand

from fdi.models import ImportLog, InvestmentLoad
from dateutil.parser import parse


def valid_date(s):
    """ Validates input date format to be YYYY-MM-DDTHH:Mi:SSZ, as API strictly expects it like that"""
    try:
        return parse(s)
    except ValueError:
        msg = "Not a valid date: '{0}'. Expected format is YYYY-MM-DDTHH:Mi:SSZ".format(
            s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = 'Import projects from Data Hub API'

    def add_arguments(self, parser):
        parser.add_argument(
            "--startdate", help="Start Date - format YYYY-MM-DDTHH:Mi:SS", required=True, type=valid_date,
        )
        parser.add_argument(
            "--enddate", help="End Date - format YYYY-MM-DDTHH:Mi:SS", required=False, type=valid_date
        )

    def get_api_results(self, startdate, enddate=None):
        CLIENT_ID = settings.DH_CLIENT_ID
        CLIENT_SECRET = settings.DH_CLIENT_SECRET
        TOKEN_URL = settings.DH_TOKEN_URL
        INVEST_URL = settings.DH_INVEST_URL
        response = requests.post(
            TOKEN_URL,
            data={'grant_type': 'client_credentials'},
            auth=(CLIENT_ID, CLIENT_SECRET))

        token = response.json()['access_token']
        params = {'modified_on__gte': startdate}

        if enddate:
            params['modified_on__lte'] = enddate

        response = requests.get(
            INVEST_URL,
            params=params,
            headers={'Authorization': f'bearer {token}'}
        )
        return response

    def handle(self, *args, **options):
        full_import = True
        startdate = options["startdate"]
        enddate = options.get("enddate")
        full_import = False
        response = self.get_api_results(startdate, enddate=enddate)
        metadata = {"request_time": datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%SZ"),
                    "startdate": datetime.strftime(startdate, "%Y-%m-%dT%H:%M:%SZ"),
                    "status": response.status_code}
        import_log = ImportLog(full=full_import)
        if response.status_code == 200:
            json_data = response.json()
            metadata["size"] = json_data["count"]
            import_log.metadata = metadata
            import_log.save()
            to_create = []
            for idx, record in enumerate(json_data["results"]):
                defaults = {"row_index": idx, "import_id": import_log}
                to_create.append(InvestmentLoad(data=record, **defaults))
            with transaction.atomic():
                transaction.on_commit(lambda: print("transaction complete"))
                print(f"creating {len(to_create)} rows")
                InvestmentLoad.objects.bulk_create(to_create, batch_size=500)
        else:
            print(f"API response {response.status_code}")
