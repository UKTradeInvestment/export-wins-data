import requests
from django.conf import settings
from django.db import transaction
from django.core.management import BaseCommand

from urlobject import URLObject

from fdi.models import (
    UKRegion,
    Sector,
    Country
)


class Command(BaseCommand):
    help = 'Import project metadata from Data Hub API'
    MODELS = {
        './uk-region/': UKRegion,
        './sector/': Sector,
        './country/': Country,
    }

    @transaction.atomic()
    def import_api_results(self, endpoint, model):
        base_url = URLObject(settings.DH_METADATA_URL)
        meta_url = base_url.relative(endpoint)

        response = requests.get(meta_url, verify=not settings.DEBUG)
        if response.ok:
            results = response.json()
            for result in results:
                print(result)
                model_instance, created = model.objects.get_or_create(id=result['id'], defaults=result)
                updated = False
                for field in ['name', 'disabled_on']:
                    if getattr(model_instance, field) != result[field]:
                        setattr(model_instance, field, result[field])
                        updated = True
                if updated:
                    model_instance.save()

    def handle(self, *args, **options):

        for endpoint, model in self.MODELS.items():
            self.import_api_results(endpoint, model)
