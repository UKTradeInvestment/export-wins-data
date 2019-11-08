from django.urls import path

from datasets.views import WinsDatasetView, AdvisorsDatasetView, BreakdownsDatasetView


urlpatterns = [
    path('advisors', AdvisorsDatasetView.as_view(), name='advisors-dataset'),
    path('breakdowns', BreakdownsDatasetView.as_view(), name='breakdowns-dataset'),
    path('wins', WinsDatasetView.as_view(), name='wins-dataset'),
]
