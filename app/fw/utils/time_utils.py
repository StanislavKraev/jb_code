# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime, timedelta
import pytz


def calc_fixed_time_not_earlier(start_dt, desired_time_str, timeout_td, timezone_name):
    eta = copy(start_dt)
    eta = eta.replace(tzinfo=pytz.utc)
    eta = datetime.astimezone(eta, pytz.timezone(timezone_name))
    eta += timeout_td

    if desired_time_str:
        desired_time = datetime.strptime(desired_time_str, "%H:%M")
        dt = eta.replace(hour=desired_time.hour, minute=desired_time.minute)
        if dt < eta:
            dt += timedelta(days=1)
        eta = dt
    eta = eta.astimezone(pytz.utc).replace(tzinfo=None)

    return eta
