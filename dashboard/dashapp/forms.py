from datetime import datetime, time, timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    ActionPoint,
    ActionPointAssignment,
    CalendarEvent,
    Comment,
    NotificationPreference,
    ProgressUpdate,
    UploadedDocument,
    WorkerUser,
)


ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv'}
ALLOWED_DOCUMENT_CONTENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    'application/csv',
}


class ActionPointForm(forms.ModelForm):
    assignees = forms.ModelMultipleChoiceField(
        queryset=WorkerUser.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text='Select one or more registered workers.',
    )

    class Meta:
        model = ActionPoint
        fields = ['title', 'description', 'status', 'priority', 'week_start', 'due_date']
        widgets = {
            'week_start': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        week_start = cleaned_data.get('week_start')
        due_date = cleaned_data.get('due_date')
        if week_start and due_date and due_date < week_start:
            raise forms.ValidationError('Due date cannot be before week start.')
        return cleaned_data


class ActionPointAssignmentForm(forms.ModelForm):
    class Meta:
        model = ActionPointAssignment
        fields = ['assignee', 'notes']


class AlertCreateForm(forms.Form):
    title = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)
    recipients = forms.ModelMultipleChoiceField(
        queryset=WorkerUser.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Leave blank to send to every active worker.',
    )


class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = ['update_text', 'status', 'percent_complete']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['message']


class CalendarEventForm(forms.ModelForm):
    SCHEDULE_WHOLE_DAY = 'whole_day'
    SCHEDULE_HOURS = 'hours'
    RECURRENCE_NONE = 'none'
    RECURRENCE_CUSTOM = 'custom'

    event_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text='Used when the event is not whole day.',
    )
    schedule_type = forms.ChoiceField(
        choices=[
            (SCHEDULE_WHOLE_DAY, 'Whole day (8:00 AM - 5:00 PM)'),
            (SCHEDULE_HOURS, 'Number of hours'),
        ],
        initial=SCHEDULE_WHOLE_DAY,
    )
    duration_hours = forms.DecimalField(
        required=False,
        min_value=0.25,
        max_value=24,
        decimal_places=2,
        max_digits=5,
        help_text='Used only when Number of hours is selected.',
    )
    recurrence_pattern = forms.ChoiceField(
        choices=[
            (RECURRENCE_NONE, 'No repeat'),
            (CalendarEvent.RECURRENCE_WEEKLY, 'Weekly'),
            (CalendarEvent.RECURRENCE_MONTHLY, 'Monthly'),
            (CalendarEvent.RECURRENCE_YEARLY, 'Yearly'),
            (RECURRENCE_CUSTOM, 'Custom'),
        ],
        initial=RECURRENCE_NONE,
    )
    custom_recurrence = forms.ChoiceField(
        choices=CalendarEvent.RECURRENCE_CHOICES,
        required=False,
        help_text='Used only when Custom is selected.',
    )
    owner = forms.ModelChoiceField(
        queryset=WorkerUser.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        required=False,
        label='For worker',
        help_text='Admins can choose whose calendar this event belongs to.',
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        instance = kwargs.get('instance')
        if instance and instance.pk:
            local_start = timezone.localtime(instance.start_datetime)
            local_end = timezone.localtime(instance.end_datetime)
            duration = local_end - local_start
            self.fields['event_date'].initial = local_start.date()
            self.fields['start_time'].initial = local_start.time().replace(second=0, microsecond=0)
            if local_start.time() == time(8, 0) and local_end.time() == time(17, 0):
                self.fields['schedule_type'].initial = self.SCHEDULE_WHOLE_DAY
            else:
                self.fields['schedule_type'].initial = self.SCHEDULE_HOURS
                self.fields['duration_hours'].initial = round(duration.total_seconds() / 3600, 2)
            if instance.recurrence in [CalendarEvent.RECURRENCE_WEEKLY, CalendarEvent.RECURRENCE_MONTHLY, CalendarEvent.RECURRENCE_YEARLY]:
                self.fields['recurrence_pattern'].initial = instance.recurrence
            elif instance.recurrence != CalendarEvent.RECURRENCE_NONE:
                self.fields['recurrence_pattern'].initial = self.RECURRENCE_CUSTOM
                self.fields['custom_recurrence'].initial = instance.recurrence
            self.fields['recurrence_until'].initial = instance.recurrence_until
            self.fields['recurrence_interval'].initial = instance.recurrence_interval
            if 'owner' in self.fields:
                self.fields['owner'].initial = instance.owner or current_user
        if not current_user or not (
            current_user.is_superuser or current_user.position == WorkerUser.POSITION_ADMIN
        ):
            self.fields.pop('owner')

    class Meta:
        model = CalendarEvent
        fields = [
            'title',
            'description',
            'location',
            'visibility',
            'owner',
            'event_date',
            'start_time',
            'schedule_type',
            'duration_hours',
            'recurrence_pattern',
            'custom_recurrence',
            'recurrence_interval',
            'recurrence_until',
        ]
        widgets = {
            'recurrence_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        start_time_value = cleaned_data.get('start_time')
        schedule_type = cleaned_data.get('schedule_type')
        duration_hours = cleaned_data.get('duration_hours')
        recurrence_pattern = cleaned_data.get('recurrence_pattern')
        custom_recurrence = cleaned_data.get('custom_recurrence')
        recurrence_until = cleaned_data.get('recurrence_until')
        owner = cleaned_data.get('owner')

        if event_date:
            if schedule_type == self.SCHEDULE_WHOLE_DAY:
                start_datetime = timezone.make_aware(datetime.combine(event_date, time(8, 0)))
                end_datetime = timezone.make_aware(datetime.combine(event_date, time(17, 0)))
            else:
                if not start_time_value:
                    raise forms.ValidationError('Start time is required when using number of hours.')
                if not duration_hours:
                    raise forms.ValidationError('Duration in hours is required.')
                start_datetime = timezone.make_aware(datetime.combine(event_date, start_time_value))
                end_datetime = start_datetime + timedelta(hours=float(duration_hours))

            cleaned_data['computed_start_datetime'] = start_datetime
            cleaned_data['computed_end_datetime'] = end_datetime
        else:
            start_datetime = None

        if recurrence_pattern == self.RECURRENCE_CUSTOM:
            recurrence = custom_recurrence or CalendarEvent.RECURRENCE_NONE
            if recurrence != CalendarEvent.RECURRENCE_NONE and not recurrence_until:
                raise forms.ValidationError('Custom recurrence needs an end date.')
        elif recurrence_pattern == self.RECURRENCE_NONE:
            recurrence = CalendarEvent.RECURRENCE_NONE
            cleaned_data['recurrence_until'] = None
        else:
            recurrence = recurrence_pattern

        cleaned_data['computed_recurrence'] = recurrence
        if recurrence != CalendarEvent.RECURRENCE_NONE and recurrence_until and start_datetime:
            if recurrence_until < start_datetime.date():
                raise forms.ValidationError('Recurrence end date cannot be before start date.')
        if 'owner' in self.fields and not owner:
            cleaned_data['owner'] = self.current_user

        return cleaned_data

    def apply_schedule(self, event):
        event.start_datetime = self.cleaned_data['computed_start_datetime']
        event.end_datetime = self.cleaned_data['computed_end_datetime']
        event.recurrence = self.cleaned_data['computed_recurrence']
        event.recurrence_until = self.cleaned_data.get('recurrence_until')
        return event


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ['in_app_enabled', 'email_enabled']


class UploadedDocumentForm(forms.ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ['title', 'category', 'description', 'visibility', 'file']

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        suffix = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else ''
        extension = f'.{suffix}' if suffix else ''
        content_type = getattr(uploaded_file, 'content_type', '')
        max_size = getattr(settings, 'MAX_DOCUMENT_UPLOAD_SIZE', 10 * 1024 * 1024)

        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise ValidationError('Upload a PDF, Word, Excel, PowerPoint, text, or CSV document.')
        if content_type and content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
            raise ValidationError('This file type is not allowed.')
        if uploaded_file.size > max_size:
            raise ValidationError('The file is too large. Maximum allowed size is 10 MB.')

        return uploaded_file


class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = WorkerUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'position_other', 'department']

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get('position')
        position_other = cleaned_data.get('position_other')
        if position == WorkerUser.POSITION_OTHER and not position_other:
            raise ValidationError('Please mention the post when selecting Other.')
        if position != WorkerUser.POSITION_OTHER:
            cleaned_data['position_other'] = ''
        return cleaned_data
