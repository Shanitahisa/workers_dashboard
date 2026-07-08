from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from dashapp.models import ActionPoint, CalendarEvent, Notification
from dashapp.services.notifications import create_notification
from dashapp.utils.recurrence import expand_events_for_range


class Command(BaseCommand):
    help = 'Generate reminders for overdue action points and upcoming events.'

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        soon = now + timedelta(days=2)

        overdue_items = ActionPoint.objects.filter(
            due_date__lt=today,
            status__in=[ActionPoint.STATUS_TODO, ActionPoint.STATUS_IN_PROGRESS, ActionPoint.STATUS_BLOCKED],
        ).prefetch_related('assignments__assignee')

        overdue_count = 0
        for action_point in overdue_items:
            assignees = {assignment.assignee for assignment in action_point.assignments.all()}
            assignees.add(action_point.created_by)
            for recipient in assignees:
                create_notification(
                    recipient=recipient,
                    title='Overdue action point reminder',
                    message=f'Action point is overdue: {action_point.title}',
                    kind=Notification.KIND_REMINDER,
                    action_point=action_point,
                )
                overdue_count += 1

        events = CalendarEvent.objects.all()
        upcoming_occurrences = expand_events_for_range(events, now, soon)

        event_count = 0
        for event, start, _ in upcoming_occurrences:
            create_notification(
                recipient=event.created_by,
                title='Upcoming event reminder',
                message=f'Event "{event.title}" starts at {start:%Y-%m-%d %H:%M}.',
                kind=Notification.KIND_EVENT,
                event=event,
            )
            event_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Reminders generated. Overdue notifications: {overdue_count}, event notifications: {event_count}'
            )
        )
