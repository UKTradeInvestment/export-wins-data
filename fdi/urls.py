from django.conf.urls import url

from fdi.views import FDISectorTeamListView

urlpatterns = [
    url(r"^sector_teams/$", FDISectorTeamListView.as_view(), name="sector_teams"),
]
