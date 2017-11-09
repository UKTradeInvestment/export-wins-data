from extended_choices import Choices

# noinspection PyTypeChecker
FILE_TYPES = Choices(
    ("EXPORT_WINS", 1, "Export Wins", {'prefix': 'export-wins', 'ns': 'ew'}),

    ("FDI_MONTHLY", 2, "FDI Investments Monthly", {
     'prefix': 'fdi/monthly', 'ns': 'fdi_monthly'}),
    ("FDI_DAILY", 3, "FDI Investments Daily", {
     'prefix': 'fdi/daily', 'ns': 'fdi_daily'}),

    ("SERVICE_DELIVERIES_MONTHLY", 4, "Service Deliveries Monthly",
     {'prefix': 'service-deliveries/monthly', 'ns': 'sd_monthly'}),
    ("SERVICE_DELIVERIES_DAILY", 5, "Service Deliveries Daily",
     {'prefix': 'service-deliveries/daily', 'ns': 'sd_daily'}),

    ("CONTACTS", 6, "Contacts", {'prefix': 'contacts',
                                 'ns': 'contacts', 'metadata_keys': ['region']}),
    ("COMPANIES", 7, "Companies", {
     'prefix': 'companies', 'ns': 'companies', 'metadata_keys': ['region']})
)

FILE_TYPES.add_subset('EW', ('EXPORT_WINS',))
FILE_TYPES.add_subset('FDI', ('FDI_MONTHLY', 'FDI_DAILY',))
FILE_TYPES.add_subset(
    'SDI', ('SERVICE_DELIVERIES_MONTHLY', 'SERVICE_DELIVERIES_DAILY',))
FILE_TYPES.add_subset('CONT', ('CONTACTS',))
FILE_TYPES.add_subset('COMP', ('COMPANIES',))
