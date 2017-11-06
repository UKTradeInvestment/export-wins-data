from django.conf.urls import url

from csv.views import (
    CSVFileView,
    CSVFilesListView,
    LatestCSVFileView,
    GenerateOTUForCSVFileView
)


urlpatterns = [
    url(r"^export-wins/$", CSVFileView.as_view(file_type='export_wins'),
        name='ew_csv_upload'),
    url(r"^export-wins/list/$",
        CSVFilesListView.as_view(file_type='export_wins'), name='ew_csv_list'),
    url(r"^export-wins/latest/$",
        LatestCSVFileView.as_view(file_type='export_wins'), name='ew_csv_latest'),
    # generate One Time URL for downloading EW CSV
    url(r"^export-wins/generate_otu/(?P<file_id>\d+)/$",
        GenerateOTUForCSVFileView.as_view(file_type='export_wins'),
        name='ew_csv_generate_otu'),
]
