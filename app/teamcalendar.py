"""Week/month grouping for the team calendar — pure date-range math. Task
due dates already live in `tasks.due_at` (store.py); this just figures out
which dates to show and their Unix-timestamp bounds for a query.
"""

import calendar
import datetime as dt


def week_days(offset=0):
    """The 7 dates (Mon..Sun) of the week `offset` weeks from this one."""
    today = dt.date.today()
    monday = today - dt.timedelta(days=today.weekday()) + dt.timedelta(weeks=offset)
    return [monday + dt.timedelta(days=i) for i in range(7)]


def month_weeks(offset=0):
    """The weeks (each 7 dates, padded into neighbouring months) covering
    the month `offset` months from this one, plus that month's first day."""
    today = dt.date.today()
    month_index = today.year * 12 + (today.month - 1) + offset
    year, month = divmod(month_index, 12)
    month += 1
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    return weeks, dt.date(year, month, 1)


def day_bounds(d):
    """(start, end) Unix timestamps spanning local calendar day `d`."""
    start = dt.datetime.combine(d, dt.time.min).timestamp()
    end = dt.datetime.combine(d + dt.timedelta(days=1), dt.time.min).timestamp()
    return start, end
