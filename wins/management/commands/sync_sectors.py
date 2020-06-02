import logging

from django.core.management.base import BaseCommand

from mi.models import Sector as SectorModel
from wins.constants import _SECTORS

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def compare_sectors(self):
        for sector_id, sector_name in _SECTORS:
            try:
                sector = SectorModel.objects.get(id=sector_id)
            except SectorModel.DoesNotExist:
                self.stdout.write(f'Sector {sector_id}:  DOES NOT EXIST : [{sector_name}]')
            else:
                if sector.name != sector_name:
                    self.stdout.write(
                        f'Sector {sector_id}: NAME CHANGE : [{sector.name} to {sector_name}]'
                    )

    def handle(self, *args, **options):
        self.compare_sectors()
