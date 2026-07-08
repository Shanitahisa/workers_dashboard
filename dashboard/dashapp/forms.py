from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

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


class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = ['update_text', 'status', 'percent_complete']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['message']


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = [
            'title',
            'description',
            'location',
            'start_datetime',
            'end_datetime',
            'visibility',
            'recurrence',
            'recurrence_interval',
            'recurrence_until',
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recurrence_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        recurrence = cleaned_data.get('recurrence')
        recurrence_until = cleaned_data.get('recurrence_until')

        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise forms.ValidationError('Event end time must be after start time.')

        if recurrence and recurrence != CalendarEvent.RECURRENCE_NONE and recurrence_until and start_datetime:
            if recurrence_until < start_datetime.date():
                raise forms.ValidationError('Recurrence end date cannot be before start date.')

        return cleaned_data


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
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'department']
