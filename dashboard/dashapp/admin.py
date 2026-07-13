from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
	ActionPoint,
	ActionPointAssignment,
	CalendarEvent,
	Comment,
	Notification,
	NotificationPreference,
	ProgressUpdate,
	UploadedDocument,
	WorkerUser,
)


@admin.register(WorkerUser)
class WorkerUserAdmin(UserAdmin):
	list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'position', 'position_other', 'department', 'is_staff')
	search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'position', 'position_other')
	list_filter = ('position', 'department', 'is_staff', 'is_superuser', 'is_active')
	fieldsets = UserAdmin.fieldsets + (
		(
			'COFTU Profile',
			{
				'fields': ('phone', 'position', 'position_other', 'department'),
			},
		),
	)
	add_fieldsets = UserAdmin.add_fieldsets + (
		(
			'COFTU Profile',
			{
				'classes': ('wide',),
				'fields': ('email', 'first_name', 'last_name', 'phone', 'position', 'position_other', 'department'),
			},
		),
	)


@admin.register(ActionPoint)
class ActionPointAdmin(admin.ModelAdmin):
	list_display = ('title', 'status', 'priority', 'week_start', 'due_date', 'created_by')
	list_filter = ('status', 'priority', 'week_start', 'due_date')
	search_fields = ('title', 'description', 'created_by__username')


@admin.register(ActionPointAssignment)
class ActionPointAssignmentAdmin(admin.ModelAdmin):
	list_display = ('action_point', 'assignee', 'assigned_by', 'assigned_at')
	list_filter = ('assigned_at',)
	search_fields = ('action_point__title', 'assignee__username', 'assigned_by__username')


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
	list_display = ('assignment', 'updated_by', 'status', 'percent_complete', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('assignment__action_point__title', 'updated_by__username', 'update_text')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ('action_point', 'author', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('action_point__title', 'author__username', 'message')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
	list_display = ('title', 'owner', 'created_by', 'location', 'start_datetime', 'end_datetime', 'visibility', 'recurrence')
	list_filter = ('visibility', 'recurrence', 'start_datetime')
	search_fields = ('title', 'location', 'description', 'owner__username', 'created_by__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('recipient', 'title', 'kind', 'is_read', 'created_at')
	list_filter = ('kind', 'is_read', 'created_at')
	search_fields = ('recipient__username', 'title', 'message')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
	list_display = ('user', 'in_app_enabled', 'email_enabled', 'updated_at')
	list_filter = ('in_app_enabled', 'email_enabled')
	search_fields = ('user__username', 'user__email')


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'visibility', 'uploaded_by', 'uploaded_at', 'file_size')
	list_filter = ('category', 'visibility', 'uploaded_at')
	search_fields = ('title', 'description', 'original_filename', 'uploaded_by__username')
	readonly_fields = ('original_filename', 'file_size', 'uploaded_by', 'uploaded_at')
