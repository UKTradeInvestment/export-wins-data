from django.conf.urls import url

from fdi.views import FDISectorTeamListView, FDIYearOnYearComparison

urlpatterns = [
    url(r"^sector_teams/$", FDISectorTeamListView.as_view(), name="sector_teams"),
    url(r"^overview/yoy/$", FDIYearOnYearComparison.as_view(), name="overview_yoy"),
]
