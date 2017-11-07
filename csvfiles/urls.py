from collections import defaultdict
from django.conf.urls import url

from csvfiles.constants import FILE_TYPES
from csvfiles.views import (
    ExportWinsCSVFileView,
    DataTeamCSVFileView,
    CSVFilesListView,
    LatestCSVFileView,
    GenerateOTUForCSVFileView
)

UPLOAD_VIEW_OVERRIDE = defaultdict(lambda: DataTeamCSVFileView)
UPLOAD_VIEW_OVERRIDE[FILE_TYPES.EXPORT_WINS.constant] = ExportWinsCSVFileView

urlpatterns = []

for ft in FILE_TYPES.entries:
    urlpatterns.extend([
        url(rf"^{ft.prefix}/$", UPLOAD_VIEW_OVERRIDE[ft.constant].as_view(file_type=ft.constant, metadata_keys=getattr(ft, 'metadata_keys', [])),
            name=f"{ft.ns}_csv_upload"),
        url(rf"^{ft.prefix}/list/$",
            CSVFilesListView.as_view(file_type=ft.constant), name=f'{ft.ns}_csv_list'),
        url(rf"^{ft.prefix}/latest/$",
            LatestCSVFileView.as_view(file_type=ft.constant), name=f'{ft.ns}_csv_latest'),
        # generate One Time URL for downloading CSV
        url(rf"^{ft.prefix}/generate_otu/(?P<file_id>\d+)/$",
            GenerateOTUForCSVFileView.as_view(file_type=ft.constant),
            name=f'{ft.ns}_csv_generate_otu'),
    ])
