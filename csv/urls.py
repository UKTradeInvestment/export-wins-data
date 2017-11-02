from django.conf.urls import url

from .views.export_wins_views import (
    ExportWinsCSVFile,
    LatestExportWinsCSVFile,
    GenerateOTUForExportWinsCSVFile
)


urlpatterns = [
    url(r"^export-wins/$", ExportWinsCSVFile.as_view(), name='ew_csv_upload'),
    url(r"^export-wins/latest/$",
        LatestExportWinsCSVFile.as_view(), name='ew_csv_latest'),
    # generate One Time URL for downloading EW CSV
    url(r"^export-wins/generate_otu/(?P<file_id>\d+)/$",
        GenerateOTUForExportWinsCSVFile.as_view(),
        name='ew_csv_generate_otu'),
]
