from functools import lru_cache
from logging import getLogger

from core.commands.base import CSVBaseCommand
from core.utils import parse_int, parse_int_list
from mi.models import Sector, SectorTeam


class Command(CSVBaseCommand):
    """Command to update sector sector team"""

    def _process_row(self, row, **options):
        sector_id = parse_int(row['id'])
        sector_name = row['sector']
        sector_team_ids = parse_int_list(row['teams'])
        sector_teams = self.get_sector_teams(sector_team_ids)
        sector = self.get_sector(sector_id, sector_name)

        if self.is_update_required(sector, sector_teams):
            self.update_sector(sector, sector_teams, options['simulate'])
        else:
            self.stdout.write(f'No update required [{sector_name}]')

    def is_update_required(self, sector, sector_teams):
        current_teams = list(sector.sector_team.all())
        for team in sector_teams:
            if team not in current_teams:
                return True

        if len(current_teams) != len(sector_teams):
            return False
        return False

    def get_sector_teams(self, sector_team_ids):
        return [self.get_sector_team(_id) for _id in sector_team_ids]

    @lru_cache(maxsize=None)
    def get_sector_team(self, sector_team_id):
        return SectorTeam.objects.get(pk=sector_team_id)

    def get_sector(self, sector_id, sector_name):
        return Sector.objects.get(id=sector_id, name=sector_name)

    def update_sector(self, sector, sector_teams, simulate):
        self.stdout.write(f'Updating sector [{sector.name}]')
        if simulate:
            return
        sector.sector_team.clear()
        sector.sector_team.add(*sector_teams)
        sector.save()
