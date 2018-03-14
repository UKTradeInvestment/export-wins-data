from django.conf.urls import url

from fdi.views import (
    FDISectorTeamListView,
    FDIOverview,
    FDITabOverview
)


urlpatterns = [
    url(r"^performance/$", FDIOverview.as_view(), name="overview"),
    url(r"^sector_teams/$", FDISectorTeamListView.as_view(), name="sector_teams"),
    url(r"^performance/(?P<name>[\w\-]+)/$",
        FDITabOverview.as_view(), name="tab_overview")
]
