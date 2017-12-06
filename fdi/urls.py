from django.conf.urls import url

from fdi.views import (
    FDISectorTeamListView,
    FDIYearOnYearComparison,
    FDIOverview,
    FDISectorTeamWinTable,
    FDISectorTeamOverview,
    FDISectorTeamDetailView,
    FDISectorTeamHVCDetailView,
    FDISectorTeamNonHVCDetailView
)


urlpatterns = [
    url(r"^sector_teams/$", FDISectorTeamListView.as_view(), name="sector_teams"),
    url(r"^sector_teams/overview/$", FDISectorTeamOverview.as_view(),
        name="sector_teams_overview", kwargs={'team_id': None}),
    url(r"^sector_teams/(?P<team_id>\d+)/win_table/$", FDISectorTeamWinTable.as_view(), name="sector_teams_win_table"),
    url(r"^overview/yoy/$", FDIYearOnYearComparison.as_view(), name="overview_yoy"),
    url(r"^overview/$", FDIOverview.as_view(), name="overview"),
    url(r"^sector_teams/(?P<team_id>\d+)/$",
        FDISectorTeamDetailView.as_view(), name="sector_team_detail"),
    url(r"^sector_teams/(?P<team_id>\d+)/hvc/$",
        FDISectorTeamHVCDetailView.as_view(), name="sector_team_hvc"),
    url(r"^sector_teams/(?P<team_id>\d+)/non_hvc/$",
        FDISectorTeamNonHVCDetailView.as_view(), name="sector_team_non_hvc"),
]
