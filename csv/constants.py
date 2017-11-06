from extended_choices import Choices

FILE_TYPES = Choices(
    ("EXPORT_WINS", 1, "Export Wins", {'prefix': 'export-wins', 'ns': 'ew'}),
    ("FDI_MONTHLY", 2, "FDI Investments Monthly", {'prefix': 'fdi/monthly', 'ns': 'fdi_monthly'}),
    ("FDI_DAILY", 3, "FDI Investments Daily", {'prefix': 'fdi/daily', 'ns': 'fdi_daily'}),
)
