# -*- coding: utf-8 -*-
import datetime
# TODO: This should be moved to DB and edited in admin console
# regular holidays are holidays that are happening every year
REGULAR_HOLIDAYS = {101, 102, 107, 223, 308, 501, 502, 509, 612, 1104}

IRREGULAR_HOLIDAYS = {20150102, 20150103, 20150104, 20150105, 20150106, 20150108, 20150109, 20150309, 20150504,
                      20150511}

IRREGULAR_WORKING_DAYS = set([

])


def is_working_day(day):
    """
    :param day: instance of class `date` or `datetime`
    :return: True if day is a working day (in Russia), False otherwise
    """
    if isinstance(day, datetime.datetime):
        day = day.date()
    if day.isoweekday() < 6:
        # normally: working day
        if day.month * 100 + day.day in REGULAR_HOLIDAYS or day.year * 10000 + day.month * 100 + day.day in IRREGULAR_HOLIDAYS:
            return False
        return True
    else:
        # normally: day off
        if day.year * 10000 + day.month * 100 + day.day in IRREGULAR_WORKING_DAYS:
            return True
        else:
            return False


def get_next_working_day(day):
    """
    Get next to given working day
    :param day: instance of class date or datetime
    :return: instance of class datetime
    """
    # Simply try to find the next working day
    if isinstance(day, datetime.datetime):
        day = day.date()
    while True:
        day = day + datetime.timedelta(1)
        if is_working_day(day):
            break
    return datetime.datetime(day.year, day.month, day.day)


def get_prev_working_day(day):
    """
    Get previous to given working day
    :param day: instance of class date or datetime
    :return: instance of class datetime
    """
    # Simply try to find previous working date
    if isinstance(day, datetime.datetime):
        day = day.date()
    while True:
        day = day - datetime.timedelta(1)
        if is_working_day(day):
            break
    return datetime.datetime(day.year, day.month, day.day)