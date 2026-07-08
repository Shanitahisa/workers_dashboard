from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ActionPointAssignment, Comment, ProgressUpdate, Notification
from .services.notifications import create_notification


@receiver(post_save, sender=ActionPointAssignment)
def assignment_created(sender, instance, created, **kwargs):
    if not created:
        return

    create_notification(
        recipient=instance.assignee,
        title='New action point assigned',
        message=f'You have been assigned: {instance.action_point.title}',
        kind=Notification.KIND_ASSIGNMENT,
        action_point=instance.action_point,
    )


@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    if not created:
        return

    action_point = instance.action_point
    recipients = set(action_point.assignments.values_list('assignee_id', flat=True))
    recipients.add(action_point.created_by_id)
    recipients.discard(instance.author_id)

    user_model = instance.author.__class__
    for user_id in recipients:
        create_notification(
            recipient=user_model.objects.get(pk=user_id),
            title='New comment on action point',
            message=f'{instance.author.username} commented on: {action_point.title}',
            kind=Notification.KIND_COMMENT,
            action_point=action_point,
        )


@receiver(post_save, sender=ProgressUpdate)
def progress_created(sender, instance, created, **kwargs):
    if not created:
        return

    assignment = instance.assignment
    action_point = assignment.action_point
    recipients = {assignment.assigned_by_id, action_point.created_by_id}
    recipients.discard(instance.updated_by_id)

    user_model = instance.updated_by.__class__
    for user_id in recipients:
        create_notification(
            recipient=user_model.objects.get(pk=user_id),
            title='Progress update posted',
            message=(
                f'{instance.updated_by.username} updated {action_point.title} '
                f'to {instance.percent_complete}% ({instance.get_status_display()})'
            ),
            kind=Notification.KIND_PROGRESS,
            action_point=action_point,
        )
