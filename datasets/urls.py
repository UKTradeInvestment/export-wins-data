from django.urls import path

from datasets.views import (
    WinsDatasetView,
    AdvisorsDatasetView,
    BreakdownsDatasetView,
    HVCDatasetView,
)

urlpatterns = [
    path('advisors', AdvisorsDatasetView.as_view(), name='advisors-dataset'),
    path('breakdowns', BreakdownsDatasetView.as_view(), name='breakdowns-dataset'),
    path('hvc', HVCDatasetView.as_view(), name='hvc-dataset'),
    path('wins', WinsDatasetView.as_view(), name='wins-dataset'),
]
