import csv
with open('fdi_hvc.csv') as f:
    reader = csv.reader(f, skipinitialspace=True)
    header = next(reader)
    hvc_list = [dict(zip(header, map(str, row))) for row in reader]

markets = {}
hvc_targets = {}
non_hvc_targets = {}

for hvc_dict in hvc_list:
    markets[hvc_dict['\ufeffmarket']] = hvc_dict['countries']
    hvc_targets[hvc_dict['\ufeffmarket']] = {k: int(v) for k, v in hvc_dict.items() if k != '\ufeffmarket' and k != 'countries' and v != ''}


with open('fdi_non_hvc.csv') as f:
    reader = csv.reader(f, skipinitialspace=True)
    header = next(reader)
    non_hvc_list = [dict(zip(header, map(str, row))) for row in reader]

for non_hvc_dict in non_hvc_list:
    markets[non_hvc_dict['\ufeffmarket']] = non_hvc_dict['countries']
    non_hvc_targets[non_hvc_dict['\ufeffmarket']] = {k: int(v) for k, v in non_hvc_dict.items() if k != '\ufeffmarket' and k != 'countries' and v != ''}

print(hvc_targets)
print()
print()
print(non_hvc_targets)
print()
print()
print(markets)


hvc_targets_final = {
  "Australia & New Zealand": {
    "Tech": 20,
    "Life S": 10,
    "FS": 10,
    "Renew": 4,
    "Creative": 6,
    "Retail": 10,
    "AESC": 4,
    "Agri": 4
  },
  "Austria": {
    "Infrastructure": 2,
    "Rail": 2
  },
  "Belgium (& Lux)": {
    "Renew": 2,
    "AESC": 3
  },
  "Canada": {
    "Tech": 23,
    "Life S": 4,
    "FS": 8,
    "Renew": 3,
    "Creative": 4,
    "Retail": 3,
    "AESC": 5,
    "O&G": 3,
    "Aero": 2
  },
  "China": {
    "Tech": 20,
    "Renew": 4,
    "Creative": 8,
    "Retail": 7,
    "AESC": 3,
    "Auto": 12,
    "Infrastructure": 14,
    "O&G": 4,
    "Rail": 2,
    "Nuclear": 4
  },
  "Denmark": {
    "Renew": 8
  },
  "Finland": {
    "Renew": 2,
    "Creative": 3
  },
  "France": {
    "Tech": 17,
    "Life S": 6,
    "FS": 5,
    "Renew": 6,
    "Creative": 8,
    "Retail": 5,
    "Rail": 2,
    "Aero": 5,
    "Nuclear": 7
  },
  "Germany": {
    "Life S": 5,
    "FS": 4,
    "F&D": 7,
    "Renew": 8,
    "Creative": 5,
    "Retail": 5,
    "AESC": 4,
    "Auto": 15,
    "Agri": 2,
    "Infrastructure": 3,
    "Chem": 2,
    "Rail": 2,
    "Aero": 1
  },
  "Hong Kong": {
    "FS": 6
  },
  "India": {
    "Tech": 27,
    "Life S": 12,
    "FS": 10,
    "Creative": 4,
    "Retail": 5,
    "AESC": 10,
    "Auto": 9
  },
  "Ireland": {
    "F&D": 10
  },
  "Israel": {
    "Tech": 7
  },
  "Italy": {
    "Life S": 5,
    "F&D": 8,
    "Renew": 3,
    "Creative": 6,
    "Retail": 7,
    "Auto": 4,
    "Rail": 2,
    "Aero": 2
  },
  "Japan": {
    "Tech": 19,
    "Life S": 12,
    "FS": 5,
    "F&D": 10,
    "Renew": 3,
    "Creative": 4,
    "Retail": 6,
    "AESC": 5,
    "Auto": 20,
    "Chem": 2,
    "Rail": 2,
    "Nuclear": 3
  },
  "Netherlands": {
    "F&D": 5,
    "Renew": 3,
    "AESC": 5,
    "Agri": 2
  },
  "Norway": {
    "Renew": 2,
    "O&G": 4
  },
  "Portugal": {
    "Renew": 3,
    "Creative": 4
  },
  "Singapore": {
    "FS": 5,
    "Renew": 2
  },
  "South Korea": {
    "Renew": 2
  },
  "Spain": {
    "Life S": 6,
    "FS": 8,
    "Renew": 5,
    "Retail": 3,
    "Infrastructure": 4,
    "Rail": 3
  },
  "Sweden": {
    "Renew": 3,
    "Creative": 4
  },
  "Switzerland": {
    "Life S": 6,
    "FS": 5,
    "AESC": 4,
    "Agri": 2,
    "Chem": 1
  },
  "Turkey": {
    "Tech": 13
  },
  "United States": {
    "Tech": 110,
    "Life S": 60,
    "FS": 41,
    "F&D": 16,
    "Renew": 7,
    "Creative": 36,
    "Retail": 7,
    "AESC": 10,
    "Auto": 16,
    "Agri": 5,
    "Infrastructure": 6,
    "Chem": 8,
    "O&G": 7,
    "Aero": 11,
    "Nuclear": 3,
    "Space": 4,
    "D&S ": 4
  },
  "Spain & Italy": {
    "AESC": 7
  },
  "France & Italy & Spain & Israel": {
    "Space": 7
  },
  "Portugal & Italy": {
    "Agri": 3
  },
  "Brazil & Mexico & Argentina": {
    "FS": 12
  },
  "China & Hong Kong": {
    "Life S": 20,
    "FS": 10
  },
  "UAE & Bahrain & Kuwait & Qatar & Saudi Arabia": {
    "FS": 7
  },
  "Mexico & Brazil": {
    "F&D": 6
  },
  "Sweden & Finland & Norway & Estonia": {
    "Life S": 7
  },
  "Brazil & Mexico & Argentina & Chile & Colombia": {
    "Tech": 20
  },
  "Baltics (Est, Lat, Lith) & Sweden & Finland & Norway & Denmark & Iceland": {
    "FS": 9
  }
}


non_hvc_targets_final = {'Australia & New Zealand': {'Tech': 20, 'Life S': 10, 'FS': 18, 'F&D': 4, 'Renew': 4, 'Creative': 6, 'Retail': 10, 'AESC': 4, 'Auto': 1, 'Agri': 4, 'Chem': 1, 'Marine': 1, 'D&S ': 1}, 'Bulgaria': {'Tech': 2, 'FS': 1, 'F&D': 1, 'Retail': 1}, 'Croatia': {'Tech': 2, 'Life S': 1}, 'Czech Republic': {'Tech': 2, 'Life S': 1, 'BPS': 1, 'F&D': 1, 'Renew': 1, 'AESC': 1}, 'Hungary': {'Tech': 3, 'Life S': 1, 'BPS': 2, 'Creative': 2}, 'Poland': {'Tech': 10, 'Life S': 2, 'BPS': 2, 'Renew': 1, 'Creative': 1, 'AESC': 2, 'Infrastructure': 1, 'Rail': 1}, 'Romania': {'Tech': 2, 'FS': 1, 'Infrastructure': 1}, 'Slovakia': {'Tech': 2, 'BPS': 1, 'Retail': 1, 'AESC': 1}, 'Slovenia': {'Tech': 2, 'Life S': 1, 'Infrastructure': 1}, 'China': {'Tech': 20, 'Life S': 20, 'FS': 10, 'Renew': 4, 'Creative': 8, 'Retail': 7, 'AESC': 3, 'Auto': 12, 'Infrastructure': 14, 'O&G': 4, 'Rail': 2, 'Nuclear': 4, 'Marine': 1}, 'Hong Kong': {'FS': 6, 'Creative': 4, 'Retail': 2, 'AESC': 2, 'Auto': 2, 'Infrastructure': 5}, 'Argentina': {'Tech': 4, 'FS': 2, 'Creative': 1}, 'Brazil': {'Tech': 8, 'Life S': 3, 'FS': 8, 'F&D': 3, 'Retail': 4}, 'Chile': {'Tech': 3, 'FS': 1, 'F&D': 2, 'Creative': 1}, 'Colombia': {'Tech': 2, 'F&D': 1, 'Creative': 1, 'Retail': 1, 'Infrastructure': 1}, 'Mexico': {'Tech': 3, 'Life S': 2, 'FS': 2, 'F&D': 3, 'AESC': 1, 'Auto': 1, 'Agri': 1}, 'Peru': {}, 'Israel': {'Tech': 7, 'Life S': 2, 'FS': 9, 'Creative': 2, 'Retail': 2, 'Space': 3}, 'Italy': {'Tech': 9, 'Life S': 5, 'FS': 4, 'F&D': 8, 'Renew': 3, 'Creative': 6, 'Retail': 7, 'AESC': 4, 'Auto': 4, 'Agri': 1, 'Chem': 2, 'O&G': 2, 'Rail': 2, 'Aero': 2, 'Marine': 1, 'Space': 2}, 'Portugal': {'Tech': 5, 'Life S': 2, 'FS': 2, 'Renew': 3, 'Creative': 4, 'Agri': 2}, 'Spain': {'Tech': 10, 'Life S': 6, 'FS': 8, 'Renew': 5, 'Creative': 3, 'Retail': 3, 'AESC': 3, 'Auto': 3, 'Infrastructure': 4, 'Rail': 3, 'Space': 1}, 'Bahrain': {'FS': 1}, 'Kuwait': {'FS': 1}, 'Qatar': {'FS': 2}, 'Saudi Arabia': {'FS': 1}, 'UAE': {'FS': 2}, 'Denmark': {'Life S': 1, 'FS': 1, 'F&D': 4, 'Renew': 8, 'Retail': 2, 'AESC': 1, 'Infrastructure': 1}, 'Baltics (Est, Lat, Lith)': {'Tech': 6, 'Life S': 1, 'FS': 4, 'Creative': 2, 'AESC': 1}, 'Finland': {'Tech': 6, 'Life S': 2, 'FS': 1, 'Renew': 2, 'Creative': 3, 'AESC': 3}, 'Iceland': {'Tech': 3, 'FS': 1}, 'Norway': {'Tech': 1, 'Life S': 1, 'FS': 1, 'Renew': 2, 'Creative': 2, 'AESC': 1, 'Auto': 1, 'Chem': 1, 'O&G': 4, 'Aero': 1, 'Marine': 1}, 'Sweden': {'Tech': 3, 'Life S': 3, 'FS': 1, 'BPS': 5, 'Renew': 5, 'Creative': 4, 'Retail': 2, 'AESC': 2, 'D&S ': 1}, 'Canada': {'Tech': 23, 'Life S': 4, 'FS': 8, 'F&D': 3, 'Renew': 3, 'Creative': 4, 'Retail': 3, 'AESC': 5, 'Auto': 2, 'O&G': 3, 'Aero': 2, 'Space': 1}, 'United States': {'Tech': 110, 'Life S': 60, 'FS': 41, 'F&D': 16, 'Renew': 7, 'Creative': 36, 'Retail': 7, 'AESC': 10, 'Auto': 16, 'Agri': 8, 'Infrastructure': 6, 'Chem': 8, 'O&G': 7, 'Aero': 11, 'Nuclear': 3, 'Space': 4, 'D&S ': 4}, 'Japan': {'Tech': 19, 'Life S': 12, 'FS': 5, 'F&D': 10, 'Renew': 3, 'Creative': 4, 'Retail': 6, 'AESC': 5, 'Auto': 20, 'Chem': 2, 'Rail': 2, 'Aero': 1, 'Nuclear': 3}, 'South Korea': {'Tech': 5, 'Life S': 1, 'FS': 2, 'F&D': 2, 'Renew': 2, 'Creative': 1, 'Retail': 1, 'AESC': 3, 'Auto': 3}, 'Taiwan': {'Tech': 9, 'F&D': 2, 'Creative': 1, 'Retail': 2, 'AESC': 1, 'Auto': 2}, 'India': {'Tech': 27, 'Life S': 12, 'FS': 10, 'F&D': 4, 'Renew': 3, 'Creative': 4, 'Retail': 5, 'AESC': 10, 'Auto': 9, 'Agri': 1, 'Chem': 1, 'Aero': 1}, 'Malaysia': {'Tech': 2, 'Life S': 2, 'FS': 1, 'F&D': 1, 'Retail': 1, 'AESC': 1, 'Infrastructure': 1}, 'Philippines': {'F&D': 2, 'AESC': 1}, 'Singapore': {'Life S': 3, 'FS': 5, 'F&D': 2, 'Renew': 2, 'Retail': 2, 'Infrastructure': 3, 'O&G': 1}, 'Thailand': {'Creative': 2, 'Retail': 1, 'AESC': 2, 'O&G': 1}, 'South Africa': {'Tech': 8, 'FS': 2, 'BPS': 4, 'F&D': 6, 'Creative': 4, 'Retail': 4}, 'Kazakhstan': {}, 'Russia': {'Tech': 5, 'Life S': 2, 'FS': 3, 'AESC': 3, 'Infrastructure': 2}, 'Turkey': {'Tech': 13, 'FS': 2, 'BPS': 2, 'F&D': 2, 'Renew': 1, 'Creative': 3, 'Retail': 2, 'Auto': 2}, 'Austria': {'Tech': 4, 'Life S': 1, 'FS': 1, 'AESC': 1, 'Auto': 2, 'Infrastructure': 2, 'Rail': 2}, 'Belgium (& Lux)': {'Tech': 5, 'Life S': 2, 'FS': 2, 'F&D': 1, 'Renew': 2, 'Creative': 2, 'AESC': 3}, 'France': {'Tech': 17, 'Life S': 6, 'FS': 5, 'F&D': 3, 'Renew': 6, 'Creative': 8, 'Retail': 5, 'AESC': 2, 'Auto': 2, 'Rail': 2, 'Aero': 5, 'Nuclear': 7, 'Space': 1}, 'Germany': {'Tech': 9, 'Life S': 5, 'FS': 4, 'F&D': 7, 'Renew': 8, 'Creative': 5, 'Retail': 5, 'AESC': 4, 'Auto': 15, 'Agri': 2, 'Infrastructure': 3, 'Chem': 2, 'Rail': 2, 'Aero': 1}, 'Ireland': {'Tech': 4, 'Life S': 2, 'FS': 4, 'BPS': 2, 'F&D': 10, 'Renew': 2, 'Creative': 2, 'Retail': 2, 'AESC': 1, 'Infrastructure': 1}, 'Netherlands': {'Tech': 6, 'Life S': 2, 'FS': 2, 'F&D': 5, 'Renew': 3, 'Retail': 2, 'AESC': 5, 'Agri': 2, 'Infrastructure': 2, 'Chem': 1, 'O&G': 2}, 'Switzerland': {'Tech': 4, 'Life S': 6, 'FS': 5, 'F&D': 4, 'AESC': 4, 'Agri': 2, 'Chem': 2, 'Rail': 2}}


markets_final = {'Australia & New Zealand': 'Australia|New Zealand', 'Austria': 'Austria', 'Belgium (& Lux)': 'Belgium|Luxembourg', 'Canada': 'Canada', 'China': 'China', 'Denmark': 'Denmark', 'Finland': 'Finland', 'France': 'France', 'Germany': 'Germany', 'Hong Kong': 'Hong Kong', 'India': 'India', 'Ireland': 'Ireland', 'Israel': 'Israel', 'Italy': 'Italy', 'Japan': 'Japan', 'Netherlands': 'Netherlands', 'Norway': 'Norway', 'Portugal': 'Portugal', 'Singapore': 'Singapore', 'South Korea': 'South Korea', 'Spain': 'Spain', 'Sweden': 'Sweden', 'Switzerland': 'Switzerland', 'Turkey': 'Turkey', 'United States': 'United States', 'Spain & Italy': 'Spain|Italy', 'France & Italy & Spain & Israel': 'France|Italy|Spain|Israel', 'Portugal & Italy': 'Portugal|Italy', 'Brazil & Mexico & Argentina': 'Brazil|Mexico|Argentina', 'China & Hong Kong': 'China|Hong Kong', 'UAE & Bahrain & Kuwait & Qatar & Saudi Arabia': 'UAE|Bahrain|Kuwait|Qatar|Saudi Arabia', 'Mexico & Brazil': 'Mexico|Brazil', 'Sweden & Finland & Norway & Estonia': 'Sweden|Finland|Norway|Estonia', 'Brazil & Mexico & Argentina & Chile & Colombia': 'Brazil|Mexico|Argentina|Chile|Colombia', 'Baltics (Est, Lat, Lith) & Sweden & Finland & Norway & Denmark & Iceland': 'Estonia|Latvia|Lithuania|Sweden|Finland|Norway|Denmark|Iceland', 'Bulgaria': 'Bulgaria', 'Croatia': 'Croatia', 'Czech Republic': 'Czech Republic', 'Hungary': 'Hungary', 'Poland': 'Poland', 'Romania': 'Romania', 'Slovakia': 'Slovakia', 'Slovenia': 'Slovenia', 'Argentina': 'Argentina', 'Brazil': 'Brazil', 'Chile': 'Chile', 'Colombia': 'Colombia', 'Mexico': 'Mexico', 'Peru': 'Peru', 'Bahrain': 'Bahrain', 'Kuwait': 'Kuwait', 'Qatar': 'Qatar', 'Saudi Arabia': 'Saudi Arabia', 'UAE': 'UAE', 'Baltics (Est, Lat, Lith)': 'Estonia|Latvia|Lithuania', 'Iceland': 'Iceland', 'Taiwan': 'Taiwan', 'Malaysia': 'Malaysia', 'Philippines': 'Philippines', 'Thailand': 'Thailand', 'South Africa': 'South Africa', 'Kazakhstan': 'Kazakhstan', 'Russia': 'Russia'}