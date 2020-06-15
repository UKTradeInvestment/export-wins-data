import time
from functools import lru_cache

from django.core.exceptions import ObjectDoesNotExist

from core.commands.base import CSVBaseCommand
from core.utils import parse_int, parse_uuid
from mi.models import Sector
from wins.models import Win


class Command(CSVBaseCommand):
    """Command to update export wins sectors """

    wins_updated = 0
    wins_skipped = 0
    wins_errors = 0

    def _process_row(self, row, **options):
        win_id = parse_uuid(row['win_id'])
        old_sector_id = parse_int(row['old_sector_id'])
        new_sector_id = parse_int(row['new_sector_id'])

        if old_sector_id != new_sector_id:
            try:
                sector = self.get_sector(new_sector_id)
                win = self.get_win(win_id)
                self.update_win(win, sector, options['simulate'])
                self.wins_updated += 1
            except ObjectDoesNotExist:
                self.wins_errors += 1
                self.stdout.write(
                    self.style.WARNING(f'Skipping due to an invalid ID ({win_id}/{new_sector_id})')
                )
        else:
            self.wins_skipped += 1
            self.stdout.write(f'No update required for win {win_id}')

    def handle(self, *args, **options):
        total_records = Win.objects.count()
        start = time.perf_counter()
        super().handle(*args, **options)
        end = time.perf_counter()
        self.stdout.write(
            self.style.SUCCESS(
                f'Update completed in {end - start:0.4f} seconds.\n'
                f'  - Total records: {total_records}\n'
                f'  - Unprocessed: {total_records-self.wins_updated-self.wins_skipped} \n'
                f'  - Updated: {self.wins_updated}\n'
                f'  - Skipped: {self.wins_skipped}\n'
                f'  - Errors: {self.wins_errors}',
            ),
        )

    @lru_cache(maxsize=None)
    def get_sector(self, sector_id):
        return Sector.objects.get(pk=sector_id)

    def get_win(self, win_id):
        return Win.objects.get(pk=win_id)

    def update_win(self, win, sector, simulate):
        if not simulate:
            win.sector = sector.id
            win.save(update_fields=['sector'])
        message = (
            f'Saved sector {sector.id} to win {win.id}'
        )
        self.stdout.write(self.style.SUCCESS(message))
