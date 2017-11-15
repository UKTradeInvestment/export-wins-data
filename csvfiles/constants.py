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

    ("CONTACTS_REGION", 6, "Contacts for Regions", {'prefix': 'contacts/region',
                                                    'ns': 'cont_region', 'metadata_keys': ['region']}),
    ("CONTACTS_SECTOR", 7, "Contacts for Sectors", {'prefix': 'contacts/sector',
                                                    'ns': 'cont_sector', 'metadata_keys': ['sector']}),
    ("COMPANIES_REGION", 8, "Companies for Regions", {
     'prefix': 'companies/region', 'ns': 'comp_region', 'metadata_keys': ['region']}),
    ("COMPANIES_SECTOR", 9, "Companies for Sectors", {
     'prefix': 'companies/sector', 'ns': 'comp_sector', 'metadata_keys': ['sector']})
)

FILE_TYPES.add_subset('EW', ('EXPORT_WINS',))
FILE_TYPES.add_subset('FDI', ('FDI_MONTHLY', 'FDI_DAILY',))
FILE_TYPES.add_subset(
    'SDI', ('SERVICE_DELIVERIES_MONTHLY', 'SERVICE_DELIVERIES_DAILY',))
FILE_TYPES.add_subset('CONT', ('CONTACTS_REGION', 'CONTACTS_SECTOR',))
FILE_TYPES.add_subset('COMP', ('COMPANIES_REGION', 'COMPANIES_SECTOR',))
