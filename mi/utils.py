import datetime


def get_financial_start_date(date=None):
    """ Returns financial year start date for a given date. Set to current date if none supplied """
    if not date:
        date = datetime.datetime.today()
    if date.month < 4:
        return datetime.datetime(date.year - 1, 4, 1)
    else:
        return datetime.datetime(date.year, 4, 1)


def get_financial_end_date(date=None):
    """ Returns financial year end date for a given date. Set to current date if none supplied """
    if not date:
        date = datetime.datetime.today()
    if date.month >= 4:
        return datetime.datetime(date.year + 1, 3, 31)
    else:
        return datetime.datetime(date.year, 3, 31)


def month_iterator(start_date, end_date=None):
    """ Helper generator function to iterate through (year, month) between given dates,
    both dates' months inclusive """
    # initialise end_date to today, if missing
    if not end_date:
        end_date = datetime.datetime.today()
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
    return (campaign['totals']['progress']['confirmed_percent'],
            campaign['totals']['progress']['unconfirmed_percent'],
            campaign['totals']['target'])


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


def lookup(dict, key, *keys):
    """
    Helper to lookup a key or nested keys within a dictionary
    :param dict:
    :param key:
    :param keys:
    :return:
    """
    if keys:
        return lookup(dict.get(key, {}), *keys)
    return dict.get(key)
