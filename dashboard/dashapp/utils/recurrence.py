from calendar import monthrange
from datetime import timedelta

from django.utils import timezone

from dashapp.models import CalendarEvent


def _add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def expand_events_for_range(events, range_start, range_end):
    expanded = []

    for event in events:
        if event.recurrence == CalendarEvent.RECURRENCE_NONE:
            if range_start <= event.start_datetime <= range_end:
                expanded.append((event, event.start_datetime, event.end_datetime))
            continue

        occurrence_start = event.start_datetime
        occurrence_end = event.end_datetime

        while occurrence_start <= range_end:
            if event.recurrence_until and occurrence_start.date() > event.recurrence_until:
                break

            if range_start <= occurrence_start <= range_end:
                expanded.append((event, occurrence_start, occurrence_end))

            if event.recurrence == CalendarEvent.RECURRENCE_DAILY:
                delta = timedelta(days=event.recurrence_interval)
                occurrence_start = occurrence_start + delta
                occurrence_end = occurrence_end + delta
            elif event.recurrence == CalendarEvent.RECURRENCE_WEEKLY:
                delta = timedelta(weeks=event.recurrence_interval)
                occurrence_start = occurrence_start + delta
                occurrence_end = occurrence_end + delta
            elif event.recurrence == CalendarEvent.RECURRENCE_MONTHLY:
                occurrence_start = _add_months(occurrence_start, event.recurrence_interval)
                occurrence_end = _add_months(occurrence_end, event.recurrence_interval)
            else:
                break

    expanded.sort(key=lambda item: item[1])
    return expanded


def upcoming_range(days=30):
    now = timezone.now()
    return now, now + timedelta(days=days)
