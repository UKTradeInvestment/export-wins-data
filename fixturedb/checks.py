from django.core.checks import register, Tags, Warning
from django.db import ProgrammingError, OperationalError

from fixturedb.utils.hvc import get_all_hvcs_referenced_by_targets


@register(Tags.database)
def check_for_missing_hvcs(app_configs, **kwargs):
    try:
        missing_hvcs = get_all_hvcs_referenced_by_targets()
    except (ProgrammingError, OperationalError):
        print('skipping check as migrations have not been run yet')
        return []

    errors = []

    if len(missing_hvcs):
        errors.append(
            Warning(
                '{hvscount} HVCs missing from database.'.format(
                    hvscount=len(missing_hvcs)
                ),
                hint='Create missing HVCs using the ./manage.py create_missing_hvcs script',
                id='fixturedb.W001'
            )
        )
    for missing in missing_hvcs:
        errors.append(
            Warning(
                'HVCs for campaign {campaign} and year {year} missing from database.'.format(
                    campaign=missing.campaign_id,
                    year=missing.financial_year
                ),
                obj=missing,
                id='fixturedb.W002'
            )
        )
    return errors
