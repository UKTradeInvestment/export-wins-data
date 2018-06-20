from operator import itemgetter
from collections import Counter

from django.core.checks import register, Tags, Error

from .constants import EXPERIENCE, GOODS_VS_SERVICES, HVO_PROGRAMMES, \
    PROGRAMMES, RATINGS, SECTORS, TEAMS, HQ_TEAM_REGION_OR_POST, WIN_TYPES, \
    BREAKDOWN_TYPES, NOTIFICATION_TYPES, TYPES_OF_SUPPORT, WITHOUT_OUR_SUPPORT, \
    WITH_OUR_SUPPORT, UK_REGIONS, EXPERIENCE_CATEGORIES, BREAKDOWN_NAME_TO_ID, UK_SUPER_REGIONS

item0getter = itemgetter(0)


def make_key_not_unique_error(obj, hint=None):
    return Error('key not unique', id='wins.E001', obj=obj, hint=hint)


def check_unique_keys(iterable, keyfunc=item0getter):
    keys = [keyfunc(x) for x in iterable]
    c = Counter(keys)
    more_than_once = [k for k, v in c.items() if v > 1]
    if more_than_once:
        return make_key_not_unique_error(iterable, hint=more_than_once)


@register(Tags.models)
def constants_check(app_configs, **kwargs):
    errors = [
        check_unique_keys(EXPERIENCE),
        check_unique_keys(GOODS_VS_SERVICES),
        check_unique_keys(HVO_PROGRAMMES),
        check_unique_keys(PROGRAMMES),
        check_unique_keys(RATINGS),
        check_unique_keys(SECTORS),
        check_unique_keys(TEAMS),  # team_type
        check_unique_keys(HQ_TEAM_REGION_OR_POST),
        check_unique_keys(WIN_TYPES),
        check_unique_keys(BREAKDOWN_TYPES),
        check_unique_keys(BREAKDOWN_NAME_TO_ID),
        check_unique_keys(NOTIFICATION_TYPES),
        check_unique_keys(TYPES_OF_SUPPORT),
        check_unique_keys(WITH_OUR_SUPPORT),
        check_unique_keys(WITHOUT_OUR_SUPPORT),
        check_unique_keys(UK_REGIONS),
        check_unique_keys(EXPERIENCE_CATEGORIES),
        check_unique_keys(UK_SUPER_REGIONS)
    ]

    return [x for x in errors if x]
