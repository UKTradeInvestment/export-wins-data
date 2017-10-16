from django_countries import Countries as DjCountries


def datahub_country_iso_code(country_name):
    """
    Here are the list of country where there is a mismatch between
    Datahub data and Django Countries
    These needs a proper fix

    Aland Islands
    BLANK
    British Virgin Islands
    Burkina
    Burma
    Cape Verde
    Congo (Democratic Republic)
    East Timor
    Falkland Islands
    Gambia, The
    Heard Island and McDonald Island
    Hong Kong (SAR)
    Ivory Coast
    Korea (North)
    Korea (South)
    Macao (SAR)
    Micronesia
    Netherlands Antilles
    Occupied Palestinian Territories
    Pitcairn, Henderson, Ducie and Oeno Islands
    Reunion
    South Georgia and South Sandwich Islands
    St Barthelemy
    St Helena
    St Kitts and Nevis
    St Lucia
    St Martin
    St Pierre and Miquelon
    St Vincent
    Sudan, South
    Surinam
    Svalbard and Jan Mayen Islands
    TEST
    United States
    Vatican City
    Virgin Islands (US)
    """
    if country_name == "United States":
        dh_country_name = "United States of America"
    elif country_name == "Korea (South)":
        dh_country_name = "South Korea"
    elif country_name == "Hong Kong (SAR)":
        dh_country_name = "Hong Kong"
    else:
        dh_country_name = country_name

    return DjCountries().by_name(dh_country_name)
