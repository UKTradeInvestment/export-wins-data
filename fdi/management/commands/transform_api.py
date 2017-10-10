from django.core.management import BaseCommand

from fdi.models.importer import InvestmentLoad
from fdi.models.live import Investments


class Command(BaseCommand):
    """
    called like this:
    ./manage.py transform_api

    it is safe to run twice as it will only import rows from fdi_investmentload where
    transform is set to false
    """

    help = 'Transform investment data from API'

    def handle(self, *args, **options):
        new_rows = 0
        updated_rows = 0
        pending_investments = InvestmentLoad.objects.filter(transformed=False)
        for pending_i in pending_investments:
            project_code = pending_i.data["project_code"]
            try:
                live_i = Investments.objects.get(project_code=project_code)
                updated_rows += 1
            except Investments.DoesNotExist:
                live_i = Investments(project_code=project_code)
                new_rows += 1

            if pending_i.data["stage"]:
                live_i.stage = pending_i.data["stage"]["name"]
            if pending_i.data["number_new_jobs"]:
                live_i.number_new_jobs = pending_i.data["number_new_jobs"]
            if pending_i.data["number_safeguarded_jobs"]:
                live_i.number_safeguarded_jobs = pending_i.data[
                    "number_safeguarded_jobs"]
            if pending_i.data["approved_high_value"]:
                live_i.approved_high_value = pending_i.data["approved_high_value"]
            if pending_i.data["approved_good_value"]:
                live_i.approved_good_value = pending_i.data["approved_good_value"]
            if pending_i.data["actual_land_date"]:
                live_i.date_won = pending_i.data["actual_land_date"]
            if pending_i.data["sector"]:
                live_i.sector_team = pending_i.data["sector"]["name"]
            if pending_i.data["uk_region_locations"] and len(pending_i.data["uk_region_locations"]) > 0:
                # taking first UK region for now. Need to understand why there would be more than one
                # and how should we be handling it, when there are more
                live_i.uk_region = pending_i.data["uk_region_locations"][0]["name"]
            if pending_i.data["client_relationship_manager"]:
                live_i.client_relationship_manager = pending_i.data[
                    "client_relationship_manager"]["name"]
            if pending_i.data["investor_company"]:
                live_i.company_name = pending_i.data["investor_company"]["name"]
                live_i.company_reference = pending_i.data["investor_company"]["id"]
            if pending_i.data["total_investment"]:
                live_i.investment_value = pending_i.data["total_investment"]
            if pending_i.data["foreign_equity_investment"]:
                live_i.foreign_equity_investment = pending_i.data[
                    "foreign_equity_investment"]
            if pending_i.data["client_relationship_manager_team"]:
                live_i.company_country = pending_i.data["client_relationship_manager_team"]
            if pending_i.data["investor_company_country"]:
                live_i.company_country = pending_i.data["investor_company_country"]
            live_i.save()
            pending_i.transformed = True
            pending_i.save()

        print("{} new projects transformed and {} existing projects updated".format(
            new_rows, updated_rows))
