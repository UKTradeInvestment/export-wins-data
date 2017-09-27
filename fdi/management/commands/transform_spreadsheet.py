from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """
    called like this:
    ./manage.py transform_spreadsheet

    it is safe to run twice as it will only import once if there are any rows with
    legacy = true it will abort. If you want to reimport then it's best to delete
    all legacy rows and run this again.
    """

    help = 'Transform investment spreadsheets'

    def handle(self, *files, **options):
        query = """
        INSERT INTO fdi_investments (project_code, stage, number_new_jobs, number_safeguarded_jobs,
        approved_high_value, approved_good_value, date_won, sector_team, uk_region, client_relationship_manager,
        company_name, company_reference, investment_value, foreign_equity_investment, legacy)
        select
          i.data->>'Project Reference Code' as project_code,
          i.data->>'Project Status' as stage,
          (i.data->>'Number Of New Jobs')::int as number_new_jobs,
          (i.data->>'Number Of Safe Jobs')::int as number_safeguarded_jobs,
          i.data->>'Project Value (New)' LIKE 'High%' as approved_high_value,
          i.data->>'Project Value (New)' LIKE 'Good%' as approved_good_value,
          to_timestamp(i.data->>' Project Decision Date', 'ISO')::date as date_won,
          i.data->>'Project Sector UKTI Sector Name' as sector_team,
          i.data->>'Project UK Region' as uk_region,
          'unknown' as client_relationship_manager,
          parent_c.data->>'Organisation Name' as company_name,
          parent_c.data->>'Organisation Reference Code' as comapny_reference,
          (i.data->>'Total Value of Investment')::DECIMAL::BIGINT as investment_value,
          (i.data->>'Foreign Equity Investment /£')::DECIMAL::BIGINT as foreign_equity_investment,
          true as legacy
        from fdi_investmentlegacyload as i
        join fdi_companylegacyload as parent_c
          on i.data ->'Project Reference Code' = parent_c.data->'Project Reference Code'
          and parent_c.data ->'Project Organisation Role' ? 'Parent'
        WHERE
          NOT EXISTS (
              SELECT id FROM fdi_investments WHERE legacy = true
            )
        ;
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            print(f'updated {cursor.rowcount} rows.')
