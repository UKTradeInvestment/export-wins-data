from datetime import datetime
import logging

from django.core.management.base import BaseCommand


from mi.models import Sector as SectorModel
from mi.sync_sectors import SyncSectors
from wins.constants import SECTORS

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--simulate", type=bool, default=False)
        parser.add_argument("--disable_on", type=datetime.fromisoformat, default=datetime.now())

    def handle(self, *args, **options):
        sync_sectors = SyncSectors(
            SectorModel, SECTORS, disable_on=options['disable_on'], simulate=options['simulate']
        )
        sync_sectors()
