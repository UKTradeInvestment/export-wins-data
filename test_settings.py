from data.settings import *  # noqa

# prevent migrations running before tests for speed and avoiding populating db
MIGRATION_MODULES = {
    'wins': None,
    'mi': None,
    'users': None,
    'auth': None,
    'contenttypes': None,
    'sessions': None,
    'messages': None,
    'admin': None,
    'authtoken': None,
}
