from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create default role groups and assign permissions.'

    def handle(self, *args, **options):
        role_names = ['Admin', 'Manager', 'Worker']
        groups = {name: Group.objects.get_or_create(name=name)[0] for name in role_names}

        app_permissions = Permission.objects.filter(content_type__app_label='dashapp')

        manager_permission_codes = {
            'add_actionpoint',
            'change_actionpoint',
            'delete_actionpoint',
            'view_actionpoint',
            'add_actionpointassignment',
            'change_actionpointassignment',
            'delete_actionpointassignment',
            'view_actionpointassignment',
            'add_progressupdate',
            'change_progressupdate',
            'view_progressupdate',
            'add_comment',
            'change_comment',
            'view_comment',
            'add_calendarevent',
            'change_calendarevent',
            'delete_calendarevent',
            'view_calendarevent',
            'view_notification',
            'change_notificationpreference',
            'view_notificationpreference',
        }

        worker_permission_codes = {
            'view_actionpoint',
            'view_actionpointassignment',
            'add_progressupdate',
            'view_progressupdate',
            'add_comment',
            'view_comment',
            'view_calendarevent',
            'view_notification',
            'change_notificationpreference',
            'view_notificationpreference',
        }

        groups['Manager'].permissions.set(
            app_permissions.filter(codename__in=manager_permission_codes)
        )
        groups['Worker'].permissions.set(
            app_permissions.filter(codename__in=worker_permission_codes)
        )

        admin_permissions = Permission.objects.all()
        groups['Admin'].permissions.set(admin_permissions)

        self.stdout.write(self.style.SUCCESS('Roles and permissions configured.'))
