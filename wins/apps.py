from django.apps import AppConfig


class WinsConfig(AppConfig):
    name = "wins"

    def ready(self):
        from . import checks
