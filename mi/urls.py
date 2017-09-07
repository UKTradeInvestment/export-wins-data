from django.conf.urls import url

from mi.views.country_views import (
    CountryListView,
    CountryDetailView,
    CountryMonthsView,
    CountryCampaignsView,
    CountryTopNonHvcWinsView,
    CountryWinTableView
)
from mi.views.parent_views import (
    ParentSectorListView,
)
from mi.views.region_views import (
    OverseasRegionsListView,
    OverseasRegionGroupListView,
    OverseasRegionOverviewView,
    OverseasRegionDetailView,
    OverseasRegionMonthsView,
    OverseasRegionCampaignsView,
    OverseasRegionsTopNonHvcWinsView,
    OverseasRegionWinTableView,
)
from mi.views.hvc_views import (
    HVCDetailView,
    HVCWinsByMarketSectorView,
    HVCWinTableView,
    GlobalHVCListView,
)
from mi.views.hvcgroup_views import (
    HVCGroupsListView,
    HVCGroupDetailView,
    HVCGroupMonthsView,
    HVCGroupCampaignsView,
    HVCGroupWinTableView,
)
from mi.views.sector_views import (
    SectorTeamCampaignsView,
    SectorTeamDetailView,
    SectorTeamsListView,
    SectorTeamMonthsView,
    SectorTeamsOverviewView,
    TopNonHvcSectorCountryWinsView,
    SectorTeamWinTableView,
)
from mi.views.team_type_views import (
    TeamTypeListView,
    TeamTypeDetailView,
    TeamTypeWinTableView,
    TeamTypeNonHvcWinsView,
    TeamTypeMonthsView,
    TeamTypeCampaignsView
)
from mi.views.global_views import GlobalWinsView
from mi.views.ukregion_views import (
    UKRegionListView,
    UKRegionDetailView,
    UKRegionWinTableView,
    UKRegionNonHvcWinsView,
    UKRegionMonthsView,
    UKRegionCampaignsView,
    UKRegionOverview
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
    url(r"^sector_teams/(?P<team_id>\d+)/win_table/$", SectorTeamWinTableView.as_view(),
        name="sector_team_win_table"),

    url(r"^parent_sectors/$", ParentSectorListView.as_view(), name="parent_sectors"),

    url(r"^os_regions/$", OverseasRegionsListView.as_view(), name="overseas_regions"),
    url(r"^os_region_groups/$", OverseasRegionGroupListView.as_view(), name="overseas_region_groups"),
    url(r"^os_regions/overview/$", OverseasRegionOverviewView.as_view(), name="overseas_region_overview"),
    url(r"^os_regions/(?P<region_id>\d+)/$", OverseasRegionDetailView.as_view(), name="overseas_region_detail"),
    url(r"^os_regions/(?P<region_id>\d+)/months/$", OverseasRegionMonthsView.as_view(), name="overseas_region_monthly"),
    url(r"^os_regions/(?P<region_id>\d+)/campaigns/$", OverseasRegionCampaignsView.as_view(),
        name="overseas_region_campaigns"),
    url(r"^os_regions/(?P<region_id>\d+)/top_non_hvcs/$", OverseasRegionsTopNonHvcWinsView.as_view(),
        name="overseas_region_top_nonhvc"),
    url(r"^os_regions/(?P<region_id>\d+)/win_table/$", OverseasRegionWinTableView.as_view(),
        name="overseas_region_win_table"),

    url(r"^hvc_groups/$", HVCGroupsListView.as_view(), name="hvc_groups"),
    url(r"^hvc_groups/(?P<group_id>\d+)/$", HVCGroupDetailView.as_view(), name="hvc_group_detail"),
    url(r"^hvc_groups/(?P<group_id>\d+)/months/$", HVCGroupMonthsView.as_view(), name="hvc_group_months"),
    url(r"^hvc_groups/(?P<group_id>\d+)/campaigns/$", HVCGroupCampaignsView.as_view(), name="hvc_group_campaigns"),
    url(r"^hvc_groups/(?P<group_id>\d+)/win_table/$", HVCGroupWinTableView.as_view(), name="hvc_group_win_table"),

    url(r"^hvc/(?P<campaign_id>[\w\-]+)/$", HVCDetailView.as_view(), name="hvc_campaign_detail"),
    url(r"^hvc/(?P<campaign_id>[\w\-]+)/top_wins/$", HVCWinsByMarketSectorView.as_view(), name="hvc_top_wins"),
    url(r"^hvc/(?P<campaign_id>[\w\-]+)/win_table/$", HVCWinTableView.as_view(), name="hvc_win_table"),

    url(r"^global_hvcs/$", GlobalHVCListView.as_view(), name="global_hvcs"),
    url(r"^global_wins/$", GlobalWinsView.as_view(), name="global_wins"),
    
    url(r"^countries/$", CountryListView.as_view(), name="countries"),
    url(r"^countries/(?P<country_code>[\w\-]+)/$", CountryDetailView.as_view(), name="country_detail"),
    url(r"^countries/(?P<country_code>[\w\-]+)/months/$", CountryMonthsView.as_view(), name="country_monthly"),
    url(r"^countries/(?P<country_code>[\w\-]+)/campaigns/$", CountryCampaignsView.as_view(), name="country_campaigns"),
    url(r"^countries/(?P<country_code>[\w\-]+)/top_non_hvcs/$", CountryTopNonHvcWinsView.as_view(), name="country_top_nonhvc"),
    url(r"^countries/(?P<country_code>[\w\-]+)/win_table/$", CountryWinTableView.as_view(), name="country_win_table"),

    url(r"^posts/$", TeamTypeListView.as_view(team_type='post'), name="post"),
    url(r"^posts/(?P<team_slug>[\w\-]+)/$", TeamTypeDetailView.as_view(team_type='post'), name="post_detail"),
    url(r"^posts/(?P<team_slug>[\w\-]+)/win_table/$", TeamTypeWinTableView.as_view(team_type='post'),
        name="post_win_table"),
    url(r"^posts/(?P<team_slug>[\w\-]+)/top_non_hvcs/$", TeamTypeNonHvcWinsView.as_view(team_type='post'),
        name="posts_top_nonhvc"),
    url(r"^posts/(?P<team_slug>[\w\-]+)/months/$", TeamTypeMonthsView.as_view(team_type='post'),
        name="posts_months"),
    url(r"^posts/(?P<team_slug>[\w\-]+)/campaigns/$", TeamTypeCampaignsView.as_view(team_type='post'),
        name="posts_campaigns"),

    url(r"^uk_regions/$", UKRegionListView.as_view(team_type='itt'), name="uk_regions"),
    url(r"^uk_regions/overview/$", UKRegionOverview.as_view(team_type='itt'), name="uk_regions"),
    url(r"^uk_regions/(?P<team_slug>[\w\-]+)/$", UKRegionDetailView.as_view(team_type='itt'),
        name="uk_regions_detail"),
    url(r"^uk_regions/(?P<team_slug>[\w\-]+)/win_table/$", UKRegionWinTableView.as_view(team_type='itt'),
        name="uk_regions_win_table"),
    url(r"^uk_regions/(?P<team_slug>[\w\-]+)/top_non_hvcs/$", UKRegionNonHvcWinsView.as_view(team_type='itt'),
        name="uk_regions_top_nonhvc"),
    url(r"^uk_regions/(?P<team_slug>[\w\-]+)/months/$", UKRegionMonthsView.as_view(team_type='itt'),
        name="uk_regions_months"),
    url(r"^uk_regions/(?P<team_slug>[\w\-]+)/campaigns/$", UKRegionCampaignsView.as_view(team_type='itt'),
        name="uk_regions_campaigns"),
]
