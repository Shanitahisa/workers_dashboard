from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def document_upload_path(instance, filename):
	suffix = Path(filename).suffix.lower()
	return f'documents/{uuid4().hex}{suffix}'


class WorkerUser(AbstractUser):
	DEPARTMENT_SECRETARIATE = 'secretariate'
	POSITION_ADMIN = 'admin'
	POSITION_ICT_ASSISTANT = 'ict_assistant'
	POSITION_LEGAL = 'legal'
	POSITION_SECRETARY_GENERAL = 'secretary_general'
	POSITION_OTHER = 'other'

	DEPARTMENT_CHOICES = [
		(DEPARTMENT_SECRETARIATE, 'Secretariate'),
	]
	POSITION_CHOICES = [
		(POSITION_ADMIN, 'Admin'),
		(POSITION_ICT_ASSISTANT, 'ICT Assistant'),
		(POSITION_LEGAL, 'Legal'),
		(POSITION_SECRETARY_GENERAL, 'Secretary General'),
		(POSITION_OTHER, 'Other'),
	]

	first_name = models.CharField(max_length=150)
	last_name = models.CharField(max_length=150)
	email = models.EmailField(unique=True)
	phone = models.CharField(max_length=30)
	position = models.CharField(max_length=40, choices=POSITION_CHOICES)
	position_other = models.CharField(max_length=120, blank=True)
	department = models.CharField(
		max_length=40,
		choices=DEPARTMENT_CHOICES,
		default=DEPARTMENT_SECRETARIATE,
	)

	REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'phone', 'position', 'department']

	def clean(self):
		super().clean()
		if self.position == self.POSITION_OTHER and not self.position_other:
			raise ValidationError({'position_other': 'Please mention the post when selecting Other.'})
		if self.position != self.POSITION_OTHER:
			self.position_other = ''

	def __str__(self):
		return f'{self.first_name} {self.last_name} ({self.username})'


class ActionPoint(models.Model):
	STATUS_TODO = 'todo'
	STATUS_IN_PROGRESS = 'in_progress'
	STATUS_BLOCKED = 'blocked'
	STATUS_DONE = 'done'

	STATUS_CHOICES = [
		(STATUS_TODO, 'To Do'),
		(STATUS_IN_PROGRESS, 'In Progress'),
		(STATUS_BLOCKED, 'Blocked'),
		(STATUS_DONE, 'Done'),
	]

	PRIORITY_LOW = 'low'
	PRIORITY_MEDIUM = 'medium'
	PRIORITY_HIGH = 'high'

	PRIORITY_CHOICES = [
		(PRIORITY_LOW, 'Low'),
		(PRIORITY_MEDIUM, 'Medium'),
		(PRIORITY_HIGH, 'High'),
	]

	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
	priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
	week_start = models.DateField()
	due_date = models.DateField()
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='created_action_points',
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['due_date', '-created_at']
		indexes = [
			models.Index(fields=['status']),
			models.Index(fields=['due_date']),
			models.Index(fields=['week_start']),
		]

	def __str__(self):
		return self.title


class ActionPointAssignment(models.Model):
	STATUS_ACTIVE = 'active'
	STATUS_DONE = 'done'
	STATUS_POSTPONED = 'postponed'

	STATUS_CHOICES = [
		(STATUS_ACTIVE, 'Active'),
		(STATUS_DONE, 'Done'),
		(STATUS_POSTPONED, 'Postponed'),
	]

	action_point = models.ForeignKey(ActionPoint, on_delete=models.CASCADE, related_name='assignments')
	assignee = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='action_assignments',
	)
	assigned_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='assigned_action_points',
	)
	notes = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
	postponed_until = models.DateField(null=True, blank=True)
	assigned_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('action_point', 'assignee')
		ordering = ['-assigned_at']
		indexes = [models.Index(fields=['assignee'])]

	def __str__(self):
		return f'{self.action_point} -> {self.assignee}'


class ProgressUpdate(models.Model):
	assignment = models.ForeignKey(ActionPointAssignment, on_delete=models.CASCADE, related_name='progress_updates')
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='progress_updates',
	)
	update_text = models.TextField()
	status = models.CharField(max_length=20, choices=ActionPoint.STATUS_CHOICES)
	percent_complete = models.PositiveSmallIntegerField(
		default=0,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.assignment} ({self.percent_complete}%)'


class Comment(models.Model):
	action_point = models.ForeignKey(ActionPoint, on_delete=models.CASCADE, related_name='comments')
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='action_point_comments',
	)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f'Comment by {self.author} on {self.action_point}'


class CalendarEvent(models.Model):
	RECURRENCE_NONE = 'none'
	RECURRENCE_DAILY = 'daily'
	RECURRENCE_WEEKLY = 'weekly'
	RECURRENCE_MONTHLY = 'monthly'
	RECURRENCE_YEARLY = 'yearly'
	VISIBILITY_PUBLIC = 'public'
	VISIBILITY_PRIVATE = 'private'

	RECURRENCE_CHOICES = [
		(RECURRENCE_NONE, 'No repeat'),
		(RECURRENCE_DAILY, 'Daily'),
		(RECURRENCE_WEEKLY, 'Weekly'),
		(RECURRENCE_MONTHLY, 'Monthly'),
		(RECURRENCE_YEARLY, 'Yearly'),
	]
	VISIBILITY_CHOICES = [
		(VISIBILITY_PUBLIC, 'Public'),
		(VISIBILITY_PRIVATE, 'Private'),
	]

	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	location = models.CharField(max_length=250, blank=True)
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField()
	visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC)
	recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default=RECURRENCE_NONE)
	recurrence_interval = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
	recurrence_until = models.DateField(null=True, blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='created_calendar_events',
	)
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name='owned_calendar_events',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['start_datetime']
		indexes = [models.Index(fields=['start_datetime'])]

	def __str__(self):
		return self.title


class Notification(models.Model):
	KIND_ASSIGNMENT = 'assignment'
	KIND_PROGRESS = 'progress'
	KIND_COMMENT = 'comment'
	KIND_EVENT = 'event'
	KIND_REMINDER = 'reminder'
	KIND_ALERT = 'alert'

	KIND_CHOICES = [
		(KIND_ASSIGNMENT, 'Assignment'),
		(KIND_PROGRESS, 'Progress Update'),
		(KIND_COMMENT, 'Comment'),
		(KIND_EVENT, 'Event'),
		(KIND_REMINDER, 'Reminder'),
		(KIND_ALERT, 'Alert'),
	]

	recipient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='notifications',
	)
	title = models.CharField(max_length=200)
	message = models.TextField()
	kind = models.CharField(max_length=20, choices=KIND_CHOICES)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	action_point = models.ForeignKey(ActionPoint, null=True, blank=True, on_delete=models.CASCADE)
	event = models.ForeignKey(CalendarEvent, null=True, blank=True, on_delete=models.CASCADE)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['recipient', 'is_read']),
			models.Index(fields=['created_at']),
		]

	def __str__(self):
		return f'{self.title} -> {self.recipient}'


class NotificationPreference(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='notification_preference',
	)
	in_app_enabled = models.BooleanField(default=True)
	email_enabled = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'Notification preferences for {self.user}'


class UploadedDocument(models.Model):
	CATEGORY_REPORT = 'report'
	CATEGORY_MINUTES = 'minutes'
	CATEGORY_POLICY = 'policy'
	CATEGORY_OTHER = 'other'
	VISIBILITY_ALL = 'all'
	VISIBILITY_MANAGERS = 'managers'
	VISIBILITY_PRIVATE = 'private'

	CATEGORY_CHOICES = [
		(CATEGORY_REPORT, 'Report'),
		(CATEGORY_MINUTES, 'Minutes'),
		(CATEGORY_POLICY, 'Policy'),
		(CATEGORY_OTHER, 'Other'),
	]
	VISIBILITY_CHOICES = [
		(VISIBILITY_ALL, 'All workers'),
		(VISIBILITY_MANAGERS, 'Managers and admins'),
		(VISIBILITY_PRIVATE, 'Uploader only'),
	]

	title = models.CharField(max_length=200)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_REPORT)
	description = models.TextField(blank=True)
	file = models.FileField(upload_to=document_upload_path)
	original_filename = models.CharField(max_length=255)
	file_size = models.PositiveIntegerField(default=0)
	visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_ALL)
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='uploaded_documents',
	)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-uploaded_at']
		indexes = [
			models.Index(fields=['category']),
			models.Index(fields=['visibility']),
			models.Index(fields=['uploaded_at']),
		]

	def __str__(self):
		return self.title
