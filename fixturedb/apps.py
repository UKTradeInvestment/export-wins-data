from django.apps import AppConfig

class FixtureDBConfig(AppConfig):
    name = 'fixturedb'

    def ready(self):
        from . import checks
