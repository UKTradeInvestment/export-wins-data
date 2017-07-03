from datetime import datetime

LAST_FIN_YEAR = datetime(2017, 3, 31)


def _today():
    """
    if the current date is past 2016-17 FY, it returns last day of 2016-17 FY
    otherwise, returns today's date.
    This is to make MI default to 2016-17 FY, even when we are in new FY.
    Until MI is ready to support multiple financial years at the same time.
    """
    if datetime.today() > LAST_FIN_YEAR:
        return LAST_FIN_YEAR

    return datetime.today()


def month_iterator(fin_year):
    """
    Helper generator function to iterate through (year, month) in a given `FinancialYear`
    """
    start_date = fin_year.start
    if fin_year.is_current:
        end_date = datetime.today()
    else:
        end_date = fin_year.end

    start_month = start_date.month - 1
    start_year = start_date.year
    end_month = end_date.month
    end_year = end_date.year
    ym_start = 12 * start_year + start_month
    ym_end = 12 * end_year + end_month
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def two_digit_float(number):
    """ Format given number into two decimal float """
    if not number:
        return None
    return float("{0:.2f}".format(number))


def sort_campaigns_by(campaign):
    """ Helper sort order function for campaigns graph """
    return (campaign["totals"]["progress"]["confirmed_percent"],
            campaign["totals"]["progress"]["unconfirmed_percent"],
            campaign["totals"]["target"])


def average(in_list):
    """ Helper function to calculate average of items in the given list """
    if len(in_list) == 0:
        return None

    return two_digit_float(sum(in_list) / len(in_list))


def percentage(part, total):
    """ Helper function to calculate percentage """
    if total == 0:
        return None
    return round(100 * part / total)


def percentage_formatted(part, total):
    return two_digit_float(percentage(part, total)) or 0


def lookup(dictionary, key, *keys):
    """
    Helper to lookup a key or nested keys within a dictionary
    """
    if keys:
        return lookup(dictionary.get(key, {}), *keys)
    return dictionary.get(key)

def print_csv(wins):
    import csv
    keys = wins[0].keys()
    with open('wins.csv', 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(wins)