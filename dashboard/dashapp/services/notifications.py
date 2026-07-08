from django.conf import settings
from django.core.mail import send_mail

from dashapp.models import Notification, NotificationPreference


def create_notification(recipient, title, message, kind, action_point=None, event=None):
    preference, _ = NotificationPreference.objects.get_or_create(user=recipient)
    notification = None

    if preference.in_app_enabled:
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            kind=kind,
            action_point=action_point,
            event=event,
        )

    if preference.email_enabled:
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email] if recipient.email else [],
            fail_silently=True,
        )

    return notification
