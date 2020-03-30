from django.urls import path

from test_helpers.mock_views import HawkViewWithScope, HawkViewWithoutScope

urlpatterns = (
    path('hawk-view-with-scope', HawkViewWithScope.as_view(), name='hawk-view-with-scope'),
    path('hawk-view-without-scope', HawkViewWithoutScope.as_view(), name='hawk-view-without-scope'),
)
