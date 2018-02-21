from collections import UserDict


class PathDict(UserDict):

    def __normalize_key(self, key):
        tkey = key
        if isinstance(key, str) and '.' in key:
            tkey = tuple(key.split('.'))
        return tkey

    def __setitem__(self, key, value):
        tkey = self.__normalize_key(key)
        return super().__setitem__(tkey, value)

    def __contains__(self, item):
        tkey = self.__normalize_key(item)
        return super().__contains__(tkey)

    def __getitem__(self, item):
        tkey = self.__normalize_key(item)
        return super().__getitem__(tkey)

    def __delitem__(self, key):
        tkey = self.__normalize_key(key)
        return super().__delitem__(tkey)
