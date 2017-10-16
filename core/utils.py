from operator import itemgetter
import itertools
from collections import defaultdict
from typing import List, MutableMapping


def filter_key(dict_, key_to_remove):
    return {k: v for k, v in dict_.items() if k != key_to_remove}


def group_by_key(l: List[MutableMapping], key: str, flatten: bool = False) -> MutableMapping:
    """
    :param l: list of dicts .e.g [{'a': 1, 'b': 1}, {'b': 2, 'a': 2}]
    :param dict_key: the dict key to group by
    :return: a dict with keys and an object or list of objects in the format:
        {1: [{'b': 1}], 2: [{'b': 2}]} or if flatten=True {1: {'b': 1}, 2: {'b': 2}}
    """
    key_getter = itemgetter(key)
    l.sort(key=key_getter)
    groups = defaultdict(list)
    for group, vals in itertools.groupby(l, key=key_getter):
        groups[group] = [filter_key(data, key) for data in vals]
    return {k: v[0] if flatten else v for k, v in groups.items()}
