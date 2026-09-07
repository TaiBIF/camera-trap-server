"""Pure-python core of the Calculation math (no Django, no DB).

Deployment.calculate() used to do the arithmetic inline, which meant every
(species, image_interval, event_interval) combination re-queried the same
images. The math lives here so both the single-cell path
(Deployment.calculate) and the bulk path (utils.save_calculation /
recalc_deployment) share one implementation and the bulk path can feed it rows
it already has in memory.

Everything here works on the raw UTC datetimes stored in the DB. The project
keeps Taiwan local time as a manual +8 shift (settings.TIME_ZONE is 'UTC'), so
month windows are shifted by hand and by_day / by_hour keep using UTC day and
hour numbers -- same as the queries this replaces.
"""

from calendar import monthrange
from datetime import datetime, timedelta, timezone as dt_timezone

TW_OFFSET = timedelta(hours=8)

# the grid every cell is stored for: 2 x 5 = 10 Calculation rows per
# (deployment, month, species)
IMAGE_INTERVALS = (30, 60)
EVENT_INTERVALS = (2, 5, 10, 30, 60)


def month_window(year, month):
    """(day_start, day_end, days_in_month) for a TW-local month, in UTC.

    day_end is the start of the next month, and both ends are inclusive in the
    queries this mirrors -- an image sitting exactly on the boundary belongs to
    both months.
    """
    days_in_month = monthrange(year, month)[1]
    day_start = datetime(year, month, 1, tzinfo=dt_timezone.utc) - TW_OFFSET
    day_end = day_start + timedelta(days=days_in_month)
    return day_start, day_end, days_in_month


def bucket_month(dt):
    """The (year, month) cell(s) a UTC image datetime falls in.

    Normally one, but a datetime landing exactly on a month boundary is
    included by both neighbouring windows (the range filter is inclusive), so
    it is counted twice -- keep that.
    """
    tw = dt + TW_OFFSET
    cells = [(tw.year, tw.month)]
    if tw.day == 1 and (tw.hour, tw.minute, tw.second, tw.microsecond) == (0, 0, 0, 0):
        prev = tw - timedelta(days=1)
        cells.append((prev.year, prev.month))
    return cells


def working_days(journal_windows, year, month):
    """Per-day 0/1 list of camera working days, from DeploymentJournal windows.

    ``journal_windows`` is an iterable of (working_start, working_end) for the
    deployment, already filtered to is_effective and not is_gap. working_start
    / working_end are stored as Taiwan time without a shift, so they are
    compared against a plain month range.
    """
    num_month = monthrange(year, month)[1]
    month_start = datetime(year, month, 1, tzinfo=dt_timezone.utc)
    month_end = datetime(year, month, num_month, tzinfo=dt_timezone.utc)
    month_stat = [0] * num_month

    for start, end in journal_windows:
        if start is None or end is None:
            continue
        if not (start <= month_end and end >= month_start):
            continue
        overlap_start = max(start, month_start)
        overlap_end = min(end, month_end)
        gap_days = (overlap_start - month_start).days
        duration_days = (overlap_end - overlap_start).days + 1
        for index in range(num_month):
            if gap_days <= index < gap_days + duration_days:
                month_stat[index] = 1
    return month_stat


def calc_payload(rows, month_stat, days_in_month, image_interval, event_interval):
    """The Calculation.data payload for one cell.

    ``rows`` is the cell's images as (datetime_utc, animal_id) ordered by
    datetime. Returns [working_days, image_count, event_count, oi1, oi2, oi3,
    pod, mdh].
    """
    sum_working_hours = sum(month_stat) * 24
    image_interval_seconds = image_interval * 60
    event_interval_seconds = event_interval * 60

    last_datetime = None
    image_count = 0  # OI3
    event_count = 0
    image_count_oi1 = 0
    delta_count = 0
    delta_count_oi1 = 0
    exist_animals = []
    days = set()       # UTC day-of-month numbers present
    day_hours = set()  # (UTC day, UTC hour) present

    for image_datetime, animal_id in rows:
        image_dt = image_datetime + TW_OFFSET
        if last_datetime:
            delta = image_dt - last_datetime
            delta_seconds = (delta.days * 86400) + delta.seconds
            delta_count += delta_seconds  # 累加
            delta_count_oi1 += delta_seconds  # 累加

            if animal_id:
                # OI1: 考慮 animal_id, animal_id 跟上一個不同, image_count 加 1
                if len(exist_animals) > 0:
                    if animal_id != exist_animals[-1]:
                        image_count_oi1 += 1
                    elif delta_count >= image_interval_seconds:
                        image_count_oi1 += 1
                        delta_count_oi1 = 0
                else:
                    exist_animals.append(animal_id)
                    image_count_oi1 += 1
            else:
                # OI3
                if delta_count >= image_interval_seconds:
                    image_count += 1
                    delta_count = 0

            if delta_seconds >= event_interval_seconds:  # 相鄰照片
                event_count += 1
        else:
            # 第一次事件 / 第一張照片, 直接加 1
            event_count = 1
            image_count = 1
            if animal_id:
                image_count_oi1 += 1

        last_datetime = image_dt
        days.add(image_datetime.day)
        day_hours.add((image_datetime.day, image_datetime.hour))

    # OI2 counts the deployment/datetime/species groups, and the loop that did
    # it never advanced its own datetime, so the count is 1 whenever the cell
    # has any image. Kept as-is so stored data stays comparable.
    image_count_oi2 = 1 if rows else 0

    oi3 = (image_count * 1.0 / sum_working_hours) * 1000 if sum_working_hours > 0 else 'N/A'
    oi1 = (image_count_oi1 * 1.0 / sum_working_hours) * 1000 if sum_working_hours > 0 else 'N/A'
    oi2 = (image_count_oi2 * 1.0 / sum_working_hours) * 1000 if sum_working_hours > 0 else 'N/A'
    # pod's numerator is by_day.count() on an unevaluated values().annotate()
    # queryset: Django drops the GROUP BY there and counts rows, so this is the
    # cell's image count, not its distinct-day count (which is what by_day
    # yields once iterated, for mdh below). Kept as-is so stored data stays
    # comparable.
    pod = len(rows) * 1.0 / sum(month_stat) if sum(month_stat) > 0 else 'N/A'

    # month, day, hour
    # note: [[0, [0]*24]] * days_in_month => call by reference error (一個改全部變)
    mdh = [[0, [0 for h in range(24)]] for x in range(days_in_month)]
    for day in days:
        if len(mdh) > day - 1:
            mdh[day - 1][0] = 1
    for day, hour in day_hours:
        if len(mdh) > day - 1:
            # shift poa timezone
            tw_hour = hour + 8 if hour < 16 else hour - 16
            mdh[day - 1][1][tw_hour] = 1

    return [month_stat, image_count, event_count, oi1, oi2, oi3, pod, mdh]
