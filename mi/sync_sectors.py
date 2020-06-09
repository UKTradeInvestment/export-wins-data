import logging

logger = logging.getLogger(__name__)


class SyncSectors:

    def __init__(self, sector_model, sectors, disable_on=None, simulate=False):
        self.sector_model = sector_model
        self.sectors = sectors
        self.disable_on = disable_on
        self.simulate = simulate

    def log(self, msg, level=logging.INFO):
        logger.log(level, msg)

    def __call__(self, *args, **kwargs):
        self.process()

    def process(self):
        self.add_new_sectors()
        self.update_existing_sectors()
        if self.disable_on:
            self.disable_sectors()

    def _get_sector(self, sector_id):
        try:
            return self.sector_model.objects.get(id=sector_id)
        except self.sector_model.DoesNotExist:
            return

    def _update_sector_name(self, sector, sector_name):
        if sector.name != sector_name:
            self.log(f'Updating Sector {sector.id}: [{sector.name} to {sector_name}]')
        if self.simulate:
            return
        sector.name = sector_name
        sector.save()

    def _create_sector(self, sector_id, sector_name):
        self.log(f'Creating Sector {sector_id}:  [{sector_name}]')
        if self.simulate:
            return
        self.sector_model.objects.create(id=sector_id, name=sector_name)

    def _disable_sector(self, sector):
        self.log(f'Disabling Sector {sector.id}: [{sector.name}]')
        if self.simulate:
            return
        sector.disabled_on = self.disable_on
        sector.save()

    def add_new_sectors(self):
        for sector_id, sector_name in self.sectors:
            sector = self._get_sector(sector_id)
            if not sector:
                self._create_sector(sector_id, sector_name)

    def update_existing_sectors(self):
        for sector_id, sector_name in self.sectors:
            sector = self._get_sector(sector_id)
            if not sector:
                self.log(f'Sector {sector_id}: DOES NOT EXIST [{sector_name}]')
            else:
                self._update_sector_name(sector, sector_name)

    def disable_sectors(self):
        sector_ids = list(dict(self.sectors).keys())
        deprecated_sectors = self.sector_model.objects.exclude(id__in=sector_ids).filter(
            disabled_on__isnull=True
        )
        for sector in deprecated_sectors:
            self._disable_sector(sector)
