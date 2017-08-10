from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.text import slugify

from mi.views.base_view import BaseWinMIView
from wins.constants import TEAMS, HQ_TEAM_REGION_OR_POST


class BaseTeamTypeMIView(BaseWinMIView):
    """ Abstract Base for other Team Type-related MI endpoints to inherit from """
    team_type = None

    @classmethod
    def as_view(cls, **initkwargs):
        # ensure team type is correct and crash early if not
        if initkwargs['team_type'] not in dict(TEAMS):
            raise ValueError('team_type is not valid')
        return super().as_view(**initkwargs)

    @cached_property
    def valid_options(self):
        return [
            {
                "slug": slugify(k.lstrip(self.team_type)),
                "id": k,
                "name": v
            }
            for k, v in HQ_TEAM_REGION_OR_POST if k.startswith(self.team_type)
        ]

    @cached_property
    def team(self):
        return [x for x in self.valid_options if x['slug'] == self.team_slug][0]

    @cached_property
    def team_type_key(self):
        """
        What to use in the result for the heading of the json response.
        Most of the time returning team_type is fine but override this if the
        database key for team type doesn't make sense
        """
        return self.team_type

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.handle_team_slug(kwargs)

    def handle_team_slug(self, kwargs):
        # ensure team_id is in team_type
        self.team_slug = kwargs.get('team_slug')
        if self.team_slug not in [x['slug'] for x in self.valid_options]:
            self._not_found(f'{self.team_slug} is not a valid {self.team_type}')

    @property
    def _team_type_result(self):
        return {
            "id": self.team['id'],
            "name": self.team['name'],
            "slug": self.team['slug'],
        }

    def _wins_filter(self):
        wf = super()._wins_filter()
        return wf & Q(team_type=self.team_type) & Q(hq_team=self.team['id'])

    def _get_all_wins(self):
        return self._hvc_wins() | self._non_hvc_wins()

    def _result(self):
        raise NotImplementedError('subclass must implement ._result')

    def get(self, request, *args, **kwargs):
        return self._success(self._result())


class TeamTypeListView(BaseTeamTypeMIView):

    def get(self, request, *args, **kwargs):
        return self._success(self.valid_options)

    def handle_team_slug(self, kwargs):
        """
        The base url doesn't have a <team_slug> so we don't need to handle it
        """
        pass


class TeamTypeDetailView(BaseTeamTypeMIView):

    def _wins_filter(self):
        wf = super()._wins_filter()
        return wf & Q(hq_team=self.team['id'])

    def _result(self):
        """
        Formatted result for a post
        """
        return {
            "id": self.team['id'],
            "name": self.team['name'],
            "slug": self.team['slug'],
            "avg_time_to_confirm": self._average_confirm_time(win__hq_team=self.team['id']),
            "wins": self._breakdowns(self._hvc_wins(), non_hvc_wins=self._non_hvc_wins(), include_non_hvc=True),
        }


class TeamTypeWinTableView(BaseTeamTypeMIView):

    def _result(self):
        return {
            self.team_type_key: {
                "id": self.team['id'],
                "name": self.team['name'],
                "slug": self.team['slug'],
            },
            "wins": self._win_table_wins(self._hvc_wins(), self._non_hvc_wins())
        }


class TeamTypeNonHvcWinsView(BaseTeamTypeMIView):

    def _result(self):
        return self._top_non_hvc(self._non_hvc_wins())
