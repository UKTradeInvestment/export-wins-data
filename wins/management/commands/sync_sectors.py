import datetime
import logging

from django.core.management.base import BaseCommand

from mi.models import Sector as SectorModel
from wins.constants import _SECTORS

logger = logging.getLogger(__name__)

DISABLE_ON = datetime.datetime(2020, 6, 1)


class Command(BaseCommand):

    def add_new_sectors(self):
        for sector_id, sector_name in _SECTORS:
            try:
                SectorModel.objects.get(id=sector_id)
            except SectorModel.DoesNotExist:
                self.stdout.write(f'Creating Sector {sector_id}:  [{sector_name}]')
                SectorModel.objects.create(id=sector_id, name=sector_name)

    def update_existing_sectors(self):
        for sector_id, sector_name in _SECTORS:
            try:
                sector = SectorModel.objects.get(id=sector_id)
            except SectorModel.DoesNotExist:
                self.stdout.write(f'Sector {sector_id}: DOES NOT EXIST [{sector_name}]')
            else:
                if sector.name != sector_name:
                    self.stdout.write(f'Updating Sector {sector_id}: [{sector_name}]')
                    sector.name = sector_name
                    sector.save()

    def disable_sectors(self):
        sector_ids = list(dict(_SECTORS).keys())
        deprecated_sectors = SectorModel.objects.exclude(id__in=sector_ids).filter(
            disabled_on__isnull=True
        )
        for sector in deprecated_sectors:
            self.stdout.write(f'Disabling Sector {sector.id}: [{sector.name}]')
            sector.disabled_on = DISABLE_ON
            sector.save()

    def handle(self, *args, **options):
        self.update_existing_sectors()
        self.add_new_sectors()
        self.disable_sectors()
