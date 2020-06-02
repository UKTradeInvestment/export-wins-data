from datetime import datetime
import logging

from django.core.management.base import BaseCommand


from mi.models import Sector as SectorModel
from mi.sync_sectors import SyncSectors
from wins.constants import SECTORS

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        sync_sectors = SyncSectors(
            SectorModel, SECTORS, disable_on=datetime.now(), simulate=False
        )
        sync_sectors()
