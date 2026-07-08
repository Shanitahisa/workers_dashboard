import mimetypes
from calendar import Calendar, month_name
from pathlib import Path

from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils.http import content_disposition_header
from django.utils import timezone

from .forms import (
	ActionPointAssignmentForm,
	ActionPointForm,
	AlertCreateForm,
	CalendarEventForm,
	CommentForm,
	NotificationPreferenceForm,
	ProgressUpdateForm,
	UploadedDocumentForm,
	WorkerProfileForm,
)
from .models import (
	ActionPoint,
	ActionPointAssignment,
	CalendarEvent,
	Comment,
	Notification,
	NotificationPreference,
	ProgressUpdate,
	UploadedDocument,
)
from .permissions import can_manage_action_points, can_update_assignment, can_view_document
from .services.notifications import create_notification
from .utils.recurrence import expand_events_for_range


def _week_start(dt):
	return dt - timedelta(days=dt.weekday())


@login_required
def profile_detail(request):
	return render(request, 'dashapp/profile/detail.html')


@login_required
def profile_edit(request):
	form = WorkerProfileForm(request.POST or None, instance=request.user)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Profile updated successfully.')
		return redirect('dashapp:profile')
	return render(request, 'dashapp/profile/form.html', {'form': form})


@require_POST
@login_required
@never_cache
def logout_view(request):
	logout(request)
	response = redirect('login')
	response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
	response['Pragma'] = 'no-cache'
	response['Expires'] = '0'
	return response


@login_required
def dashboard_home(request):
	now = timezone.now()
	week_start = _week_start(now.date())
	week_end = week_start + timedelta(days=6)

	if can_manage_action_points(request.user):
		action_points = ActionPoint.objects.filter(week_start=week_start)
	else:
		action_points = ActionPoint.objects.filter(assignments__assignee=request.user).distinct()

	events = CalendarEvent.objects.filter(
		Q(visibility=CalendarEvent.VISIBILITY_PUBLIC) | Q(created_by=request.user)
	)
	expanded_events = expand_events_for_range(events, now, now + timedelta(days=14))
	unread_alerts = Notification.objects.filter(recipient=request.user, is_read=False).count()
	documents = UploadedDocument.objects.select_related('uploaded_by')
	if request.user.is_superuser:
		pass
	elif can_manage_action_points(request.user):
		documents = documents.filter(
			Q(visibility__in=[UploadedDocument.VISIBILITY_ALL, UploadedDocument.VISIBILITY_MANAGERS])
			| Q(uploaded_by=request.user)
		)
	else:
		documents = documents.filter(Q(visibility=UploadedDocument.VISIBILITY_ALL) | Q(uploaded_by=request.user))

	context = {
		'action_points': action_points[:10],
		'expanded_events': expanded_events[:10],
		'unread_alerts': unread_alerts,
		'recent_documents': documents[:6],
		'week_start': week_start,
		'week_end': week_end,
	}
	return render(request, 'dashapp/dashboard.html', context)


@login_required
def action_point_list(request):
	query = request.GET.get('q', '').strip()
	status = request.GET.get('status', '')

	if can_manage_action_points(request.user):
		queryset = ActionPoint.objects.all()
	else:
		queryset = ActionPoint.objects.filter(assignments__assignee=request.user).distinct()

	if query:
		queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
	if status:
		queryset = queryset.filter(status=status)

	paginator = Paginator(queryset, 15)
	page_obj = paginator.get_page(request.GET.get('page'))
	return render(
		request,
		'dashapp/action_points/list.html',
		{
			'page_obj': page_obj,
			'query': query,
			'status': status,
			'status_choices': ActionPoint.STATUS_CHOICES,
		},
	)


@login_required
def action_point_create(request):
	if not can_manage_action_points(request.user):
		return HttpResponseForbidden('Not allowed')

	form = ActionPointForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		action_point = form.save(commit=False)
		action_point.created_by = request.user
		action_point.save()
		for assignee in form.cleaned_data['assignees']:
			ActionPointAssignment.objects.create(
				action_point=action_point,
				assignee=assignee,
				assigned_by=request.user,
			)
		messages.success(request, 'Action point created successfully.')
		return redirect('dashapp:action_point_detail', pk=action_point.pk)

	return render(request, 'dashapp/action_points/form.html', {'form': form})


@login_required
def action_point_detail(request, pk):
	action_point = get_object_or_404(ActionPoint, pk=pk)
	is_assigned = ActionPointAssignment.objects.filter(action_point=action_point, assignee=request.user).exists()

	if not can_manage_action_points(request.user) and not is_assigned:
		return HttpResponseForbidden('Not allowed')

	comment_form = CommentForm(request.POST or None)
	if request.method == 'POST' and 'add_comment' in request.POST and comment_form.is_valid():
		comment = comment_form.save(commit=False)
		comment.action_point = action_point
		comment.author = request.user
		comment.save()

		messages.success(request, 'Comment added.')
		return redirect('dashapp:action_point_detail', pk=action_point.pk)

	assignments = action_point.assignments.select_related('assignee', 'assigned_by')
	progress_updates = ProgressUpdate.objects.filter(assignment__action_point=action_point).select_related(
		'assignment', 'updated_by'
	)
	comments = action_point.comments.select_related('author')

	return render(
		request,
		'dashapp/action_points/detail.html',
		{
			'action_point': action_point,
			'assignments': assignments,
			'progress_updates': progress_updates,
			'comments': comments,
			'comment_form': comment_form,
			'can_manage': can_manage_action_points(request.user),
		},
	)


@login_required
def assign_action_point(request, pk):
	action_point = get_object_or_404(ActionPoint, pk=pk)
	if not can_manage_action_points(request.user):
		return HttpResponseForbidden('Not allowed')

	form = ActionPointAssignmentForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		assignment = form.save(commit=False)
		assignment.action_point = action_point
		assignment.assigned_by = request.user
		assignment.save()
		messages.success(request, 'Action point assigned successfully.')
		return redirect('dashapp:action_point_detail', pk=action_point.pk)

	return render(
		request,
		'dashapp/action_points/assign.html',
		{
			'form': form,
			'action_point': action_point,
		},
	)


@login_required
def my_assignments(request):
	assignments = ActionPointAssignment.objects.filter(assignee=request.user).select_related('action_point', 'assigned_by')
	return render(request, 'dashapp/assignments/list.html', {'assignments': assignments})


@login_required
@require_POST
def mark_assignment_done(request, pk):
	assignment = get_object_or_404(ActionPointAssignment, pk=pk)
	if not can_update_assignment(request.user, assignment):
		return HttpResponseForbidden('Not allowed')

	assignment.status = ActionPointAssignment.STATUS_DONE
	assignment.postponed_until = None
	assignment.save(update_fields=['status', 'postponed_until'])
	if not assignment.action_point.assignments.exclude(status=ActionPointAssignment.STATUS_DONE).exists():
		assignment.action_point.status = ActionPoint.STATUS_DONE
		assignment.action_point.save(update_fields=['status', 'updated_at'])
	messages.success(request, 'Assignment marked as done.')
	return redirect(request.POST.get('next') or 'dashapp:my_assignments')


@login_required
@require_POST
def postpone_assignment(request, pk):
	assignment = get_object_or_404(ActionPointAssignment, pk=pk)
	if not can_update_assignment(request.user, assignment):
		return HttpResponseForbidden('Not allowed')

	postponed_until = request.POST.get('postponed_until') or None
	assignment.status = ActionPointAssignment.STATUS_POSTPONED
	assignment.postponed_until = postponed_until
	assignment.save(update_fields=['status', 'postponed_until'])
	if assignment.action_point.status != ActionPoint.STATUS_DONE:
		assignment.action_point.status = ActionPoint.STATUS_BLOCKED
		assignment.action_point.save(update_fields=['status', 'updated_at'])
	messages.success(request, 'Assignment postponed.')
	return redirect(request.POST.get('next') or 'dashapp:my_assignments')


@login_required
def add_progress_update(request, pk):
	assignment = get_object_or_404(ActionPointAssignment, pk=pk)
	if not can_update_assignment(request.user, assignment):
		return HttpResponseForbidden('Not allowed')

	form = ProgressUpdateForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		update = form.save(commit=False)
		update.assignment = assignment
		update.updated_by = request.user
		update.save()

		action_point = assignment.action_point
		action_point.status = update.status
		action_point.save(update_fields=['status', 'updated_at'])

		messages.success(request, 'Progress update added.')
		return redirect('dashapp:action_point_detail', pk=action_point.pk)

	return render(
		request,
		'dashapp/assignments/progress_form.html',
		{
			'form': form,
			'assignment': assignment,
		},
	)


@login_required
def calendar_view(request):
	today = timezone.localdate()
	month_param = request.GET.get('month')
	try:
		if month_param:
			year, month = [int(part) for part in month_param.split('-', 1)]
		else:
			year, month = today.year, today.month
	except (TypeError, ValueError):
		year, month = today.year, today.month

	month_start = today.replace(year=year, month=month, day=1)
	weeks = Calendar(firstweekday=0).monthdatescalendar(year, month)
	start_datetime = timezone.make_aware(datetime.combine(weeks[0][0], time.min))
	end_datetime = timezone.make_aware(datetime.combine(weeks[-1][-1], time.max))
	events = CalendarEvent.objects.filter(
		Q(visibility=CalendarEvent.VISIBILITY_PUBLIC) | Q(created_by=request.user)
	)
	expanded_events = expand_events_for_range(events, start_datetime, end_datetime)
	events_by_day = {}
	for event, start, end in expanded_events:
		events_by_day.setdefault(start.date(), []).append((event, start, end))

	calendar_weeks = [
		[
			{
				'date': day,
				'in_month': day.month == month,
				'is_today': day == today,
				'events': events_by_day.get(day, []),
			}
			for day in week
		]
		for week in weeks
	]
	previous_month = (month_start - timedelta(days=1)).replace(day=1)
	next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

	return render(
		request,
		'dashapp/calendar/list.html',
		{
			'calendar_weeks': calendar_weeks,
			'month_label': f'{month_name[month]} {year}',
			'previous_month': previous_month,
			'next_month': next_month,
			'can_manage': can_manage_action_points(request.user),
		},
	)


@login_required
def calendar_event_create(request):
	if not can_manage_action_points(request.user):
		return HttpResponseForbidden('Not allowed')

	form = CalendarEventForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		event = form.save(commit=False)
		event.created_by = request.user
		event.save()
		if event.visibility == CalendarEvent.VISIBILITY_PUBLIC:
			user_model = get_user_model()
			for recipient in user_model.objects.filter(is_active=True):
				create_notification(
					recipient=recipient,
					title='New public calendar event',
					message=f'{event.title} starts on {event.start_datetime:%Y-%m-%d %H:%M}.',
					kind=Notification.KIND_EVENT,
					event=event,
				)
		messages.success(request, 'Calendar event created.')
		return redirect('dashapp:calendar')

	return render(request, 'dashapp/calendar/form.html', {'form': form})


@login_required
def alert_list(request):
	alerts = Notification.objects.filter(recipient=request.user)
	paginator = Paginator(alerts, 20)
	page_obj = paginator.get_page(request.GET.get('page'))
	return render(request, 'dashapp/alerts/list.html', {'page_obj': page_obj})


@login_required
def alert_create(request):
	form = AlertCreateForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		recipients = form.cleaned_data['recipients']
		if not recipients:
			recipients = get_user_model().objects.filter(is_active=True)
		for recipient in recipients:
			create_notification(
				recipient=recipient,
				title=form.cleaned_data['title'],
				message=form.cleaned_data['message'],
				kind=Notification.KIND_ALERT,
			)
		messages.success(request, 'Alert sent successfully.')
		return redirect('dashapp:alert_list')

	return render(request, 'dashapp/alerts/form.html', {'form': form})


@login_required
def mark_alert_read(request, pk):
	alert = get_object_or_404(Notification, pk=pk, recipient=request.user)
	alert.is_read = True
	alert.save(update_fields=['is_read'])
	return redirect('dashapp:alert_list')


@login_required
def notification_preferences(request):
	prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
	form = NotificationPreferenceForm(request.POST or None, instance=prefs)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Notification preferences updated.')
		return redirect('dashapp:notification_preferences')
	return render(request, 'dashapp/alerts/preferences.html', {'form': form})


@login_required
def document_list(request):
	query = request.GET.get('q', '').strip()
	category = request.GET.get('category', '')
	documents = UploadedDocument.objects.select_related('uploaded_by')

	if request.user.is_superuser:
		pass
	elif can_manage_action_points(request.user):
		documents = documents.filter(
			Q(visibility__in=[UploadedDocument.VISIBILITY_ALL, UploadedDocument.VISIBILITY_MANAGERS])
			| Q(uploaded_by=request.user)
		)
	else:
		documents = documents.filter(Q(visibility=UploadedDocument.VISIBILITY_ALL) | Q(uploaded_by=request.user))
	if query:
		documents = documents.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(original_filename__icontains=query))
	if category:
		documents = documents.filter(category=category)

	paginator = Paginator(documents, 12)
	page_obj = paginator.get_page(request.GET.get('page'))
	return render(
		request,
		'dashapp/documents/list.html',
		{
			'page_obj': page_obj,
			'query': query,
			'category': category,
			'category_choices': UploadedDocument.CATEGORY_CHOICES,
			'can_manage': can_manage_action_points(request.user),
		},
	)


@login_required
def document_upload(request):
	form = UploadedDocumentForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		document = form.save(commit=False)
		document.uploaded_by = request.user
		document.original_filename = Path(document.file.name).name
		document.file_size = document.file.size
		document.save()
		messages.success(request, 'Document uploaded successfully.')
		return redirect('dashapp:document_list')

	return render(request, 'dashapp/documents/form.html', {'form': form})


@login_required
def document_download(request, pk):
	document = get_object_or_404(UploadedDocument, pk=pk)
	if not can_view_document(request.user, document):
		return HttpResponseForbidden('Not allowed')

	content_type, _ = mimetypes.guess_type(document.original_filename)
	response = FileResponse(document.file.open('rb'), content_type=content_type or 'application/octet-stream')
	response['Content-Disposition'] = content_disposition_header(True, document.original_filename)
	response['X-Content-Type-Options'] = 'nosniff'
	return response
