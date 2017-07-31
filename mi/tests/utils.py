from datetime import datetime

from pytz import UTC

c = datetime.combine


def datetime_factory(date, time):
    return c(date, time).replace(tzinfo=UTC)


MIN = datetime.min.time()
MAX = datetime.max.time()
