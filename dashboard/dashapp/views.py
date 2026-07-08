import mimetypes
from pathlib import Path

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
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
	now = timezone.now()
	start = now - timedelta(days=7)
	end = now + timedelta(days=30)
	events = CalendarEvent.objects.filter(
		Q(visibility=CalendarEvent.VISIBILITY_PUBLIC) | Q(created_by=request.user)
	)
	expanded_events = expand_events_for_range(events, start, end)
	return render(request, 'dashapp/calendar/list.html', {'expanded_events': expanded_events})


@login_required
def calendar_event_create(request):
	if not can_manage_action_points(request.user):
		return HttpResponseForbidden('Not allowed')

	form = CalendarEventForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		event = form.save(commit=False)
		event.created_by = request.user
		event.save()
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
