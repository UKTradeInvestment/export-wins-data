import operator
from functools import reduce

from collections import namedtuple
from django.db.models import Q

from mi.models import Target
from wins.models import HVC

HVCStruct = namedtuple('HVCStruct', ['campaign_id', 'financial_year'])


def get_all_hvcs_referenced_by_targets(financial_years=None):
    """
    Get a list of all hvcs that need to be created that are referenced by Targets
    :param financial_years: optional, you can manually define the financial years
    instead of getting them from the Target
    :type financial_years: List[int]
    :returns a list of hvc (campaign_id, financial year) tuples that don't already exist: List[HVCStruct]
    """
    hvc_ids_expected_by_targets = Target.objects.all().values_list('campaign_id', flat=True).distinct()
    if not financial_years:
        financial_years = Target.objects.all().values_list('financial_year', flat=True).distinct()

    to_create = [
        HVCStruct(campaign_id=campaign_id,
                  financial_year=int(str(financial_year)[-2:]))
        for campaign_id in hvc_ids_expected_by_targets for financial_year in financial_years
    ]

    filter_q = reduce(
        operator.or_,
        [Q(campaign_id=data.campaign_id, financial_year=data.financial_year)
         for data in to_create]
    )

    already_existing = [
        HVCStruct(**data) for data in HVC.objects.filter(filter_q).values('campaign_id', 'financial_year')
    ]

    to_create_without_already_existing = set(to_create) - set(already_existing)

    return to_create_without_already_existing
