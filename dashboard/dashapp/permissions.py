from django.contrib.auth.models import Group


def ensure_default_groups():
    for name in ('Admin', 'Manager', 'Worker'):
        Group.objects.get_or_create(name=name)


def in_group(user, group_name):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


def can_manage_action_points(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.position in ('admin', 'ict_assistant')


def can_create_events_for_others(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.position == 'admin'


def can_update_assignment(user, assignment):
    if can_manage_action_points(user):
        return True
    return assignment.assignee_id == user.id


def can_view_document(user, document):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if document.uploaded_by_id == user.id:
        return True
    if document.visibility == 'managers' and can_manage_action_points(user):
        return True
    return document.visibility == 'all'
