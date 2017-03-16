from django.conf.urls import url

from mi.views.country_views import (
    CountryListView,
    CountryDetailView,
    CountryWinsView,
)
from mi.views.parent_views import (
    ParentSectorListView,
)
from mi.views.region_views import (
    OverseasRegionsListView,
    OverseasRegionOverviewView,
    OverseasRegionDetailView,
    OverseasRegionMonthsView,
    OverseasRegionCampaignsView,
    OverseasRegionsTopNonHvcWinsView,
)
from mi.views.hvcgroup_views import (
    HVCGroupsListView,
    HVCGroupDetailView,
    HVCGroupMonthsView,
    HVCGroupCampaignsView,
)
from mi.views.sector_views import (
    AverageTimeToConfirmView,
    SectorTeamCampaignsView,
    SectorTeamDetailView,
    SectorTeamsListView,
    SectorTeamMonthsView,
    SectorTeamsOverviewView,
    TopNonHvcSectorCountryWinsView,
)

urlpatterns = [
    url(r"^sector_teams/$", SectorTeamsListView.as_view(), name="sector_teams"),
    url(r"^sector_teams/overview/$", SectorTeamsOverviewView.as_view(), name="sector_teams_overview"),
    url(r"^sector_teams/(?P<team_id>\d+)/$", SectorTeamDetailView.as_view(), name="sector_team_detail"),
    url(r"^sector_teams/(?P<team_id>\d+)/campaigns/$", SectorTeamCampaignsView.as_view(),
        name="sector_team_campaigns"),
    url(r"^sector_teams/(?P<team_id>\d+)/months/$", SectorTeamMonthsView.as_view(),
        name="sector_team_months"),
    url(r"^sector_teams/(?P<team_id>\d+)/top_non_hvcs/$", TopNonHvcSectorCountryWinsView.as_view(),
        name="sector_team_top_non_hvc"),

    url(r"^parent_sectors/$", ParentSectorListView.as_view(), name="parent_sectors"),

    url(r"^os_regions/$", OverseasRegionsListView.as_view(), name="overseas_regions"),
    url(r"^os_regions/overview/$", OverseasRegionOverviewView.as_view(), name="overseas_region_overview"),
    url(r"^os_regions/(?P<region_id>\d+)/$", OverseasRegionDetailView.as_view(), name="overseas_region_detail"),
    url(r"^os_regions/(?P<region_id>\d+)/months/$", OverseasRegionMonthsView.as_view()),
    url(r"^os_regions/(?P<region_id>\d+)/campaigns/$", OverseasRegionCampaignsView.as_view()),
    url(r"^os_regions/(?P<region_id>\d+)/top_non_hvcs/$", OverseasRegionsTopNonHvcWinsView.as_view()),

    url(r"^hvc_groups/$", HVCGroupsListView.as_view(), name="hvc_groups"),
    url(r"^hvc_groups/(?P<group_id>\d+)/$", HVCGroupDetailView.as_view(), name="hvc_group_detail"),
    url(r"^hvc_groups/(?P<group_id>\d+)/months/$", HVCGroupMonthsView.as_view(), name="hvc_group_months"),
    url(r"^hvc_groups/(?P<group_id>\d+)/campaigns/$", HVCGroupCampaignsView.as_view(), name="hvc_group_campaigns"),

    url(r"^countries/$", CountryListView.as_view(), name="countries"),
    url(r"^countries/(?P<country_id>\d+)/$", CountryDetailView.as_view()),
    url(r"^countries/wins/$", CountryWinsView.as_view()),

    url(r"^avg_time_to_confirm/$", AverageTimeToConfirmView.as_view()),
]
