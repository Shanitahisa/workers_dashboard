# Generated manually for initial dashboard domain models.

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkerUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone', models.CharField(max_length=30)),
                ('position', models.CharField(max_length=120)),
                ('department', models.CharField(choices=[('secretariate', 'Secretariate')], default='secretariate', max_length=40)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='ActionPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('todo', 'To Do'),
                            ('in_progress', 'In Progress'),
                            ('blocked', 'Blocked'),
                            ('done', 'Done'),
                        ],
                        default='todo',
                        max_length=20,
                    ),
                ),
                (
                    'priority',
                    models.CharField(
                        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                        default='medium',
                        max_length=20,
                    ),
                ),
                ('week_start', models.DateField()),
                ('due_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='created_action_points',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['due_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('location', models.CharField(blank=True, max_length=250)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                (
                    'recurrence',
                    models.CharField(
                        choices=[
                            ('none', 'No repeat'),
                            ('daily', 'Daily'),
                            ('weekly', 'Weekly'),
                            ('monthly', 'Monthly'),
                        ],
                        default='none',
                        max_length=20,
                    ),
                ),
                (
                    'recurrence_interval',
                    models.PositiveIntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                ('recurrence_until', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='created_calendar_events',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['start_datetime'],
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('in_app_enabled', models.BooleanField(default=True)),
                ('email_enabled', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notification_preference',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='ActionPointAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                (
                    'action_point',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='assignments',
                        to='dashapp.actionpoint',
                    ),
                ),
                (
                    'assigned_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='assigned_action_points',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'assignee',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='action_assignments',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-assigned_at'],
                'unique_together': {('action_point', 'assignee')},
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'action_point',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='comments',
                        to='dashapp.actionpoint',
                    ),
                ),
                (
                    'author',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='action_point_comments',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                (
                    'kind',
                    models.CharField(
                        choices=[
                            ('assignment', 'Assignment'),
                            ('progress', 'Progress Update'),
                            ('comment', 'Comment'),
                            ('event', 'Event'),
                            ('reminder', 'Reminder'),
                        ],
                        max_length=20,
                    ),
                ),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'action_point',
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dashapp.actionpoint'),
                ),
                (
                    'event',
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dashapp.calendarevent'),
                ),
                (
                    'recipient',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProgressUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_text', models.TextField()),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('todo', 'To Do'),
                            ('in_progress', 'In Progress'),
                            ('blocked', 'Blocked'),
                            ('done', 'Done'),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    'percent_complete',
                    models.PositiveSmallIntegerField(
                        default=0,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'assignment',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progress_updates',
                        to='dashapp.actionpointassignment',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='progress_updates',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='actionpoint',
            index=models.Index(fields=['status'], name='dashapp_act_status_4bd846_idx'),
        ),
        migrations.AddIndex(
            model_name='actionpoint',
            index=models.Index(fields=['due_date'], name='dashapp_act_due_dat_fc67f4_idx'),
        ),
        migrations.AddIndex(
            model_name='actionpoint',
            index=models.Index(fields=['week_start'], name='dashapp_act_week_st_5a7ca0_idx'),
        ),
        migrations.AddIndex(
            model_name='actionpointassignment',
            index=models.Index(fields=['assignee'], name='dashapp_act_assigne_5b7b26_idx'),
        ),
        migrations.AddIndex(
            model_name='calendarevent',
            index=models.Index(fields=['start_datetime'], name='dashapp_cal_start_d_dca83f_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read'], name='dashapp_not_recipie_6af75f_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['created_at'], name='dashapp_not_created_a1ffc4_idx'),
        ),
    ]
