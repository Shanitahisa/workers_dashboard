from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ActionPoint, ActionPointAssignment, CalendarEvent, NotificationPreference


User = get_user_model()


class DashboardSmokeTests(TestCase):
	def setUp(self):
		self.manager = User.objects.create_user(
			username='manager',
			password='pass12345',
			email='manager@coftu.local',
			first_name='Manager',
			last_name='One',
			phone='0700000001',
			position='Regional Manager',
		)
		self.worker = User.objects.create_user(
			username='worker',
			password='pass12345',
			email='worker@coftu.local',
			first_name='Worker',
			last_name='One',
			phone='0700000002',
			position='Field Officer',
		)
		manager_group, _ = Group.objects.get_or_create(name='Manager')
		self.manager.groups.add(manager_group)

	def test_dashboard_requires_login(self):
		response = self.client.get(reverse('dashapp:home'))
		self.assertEqual(response.status_code, 302)

	def test_manager_can_create_action_point(self):
		self.client.login(username='manager', password='pass12345')
		response = self.client.post(
			reverse('dashapp:action_point_create'),
			{
				'title': 'Mobilize workers',
				'description': 'Organize weekly mobilization task',
				'status': ActionPoint.STATUS_TODO,
				'priority': ActionPoint.PRIORITY_HIGH,
				'week_start': date.today(),
				'due_date': date.today() + timedelta(days=2),
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(ActionPoint.objects.count(), 1)

	def test_worker_cannot_create_action_point(self):
		self.client.login(username='worker', password='pass12345')
		response = self.client.get(reverse('dashapp:action_point_create'))
		self.assertEqual(response.status_code, 403)

	def test_assignment_triggers_preference_creation(self):
		action_point = ActionPoint.objects.create(
			title='Prepare report',
			description='Weekly report compilation',
			status=ActionPoint.STATUS_TODO,
			priority=ActionPoint.PRIORITY_MEDIUM,
			week_start=date.today(),
			due_date=date.today() + timedelta(days=1),
			created_by=self.manager,
		)
		ActionPointAssignment.objects.create(
			action_point=action_point,
			assignee=self.worker,
			assigned_by=self.manager,
		)
		self.assertTrue(NotificationPreference.objects.filter(user=self.worker).exists())


class RecurrenceTests(TestCase):
	def test_monthly_event_is_saved(self):
		user = User.objects.create_user(
			username='calendar_mgr',
			password='pass12345',
			email='calendar_mgr@coftu.local',
			first_name='Calendar',
			last_name='Manager',
			phone='0700000003',
			position='Calendar Officer',
		)
		event = CalendarEvent.objects.create(
			title='Monthly coordination',
			start_datetime=timezone.make_aware(datetime.now()),
			end_datetime=timezone.make_aware(datetime.now() + timedelta(hours=1)),
			recurrence=CalendarEvent.RECURRENCE_MONTHLY,
			recurrence_interval=1,
			recurrence_until=date.today() + timedelta(days=90),
			created_by=user,
		)
		self.assertEqual(event.recurrence, CalendarEvent.RECURRENCE_MONTHLY)


class CalendarVisibilityTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			username='owner_user',
			password='pass12345',
			email='owner@coftu.local',
			first_name='Owner',
			last_name='User',
			phone='0700000010',
			position='Officer',
		)
		self.other_user = User.objects.create_user(
			username='other_user',
			password='pass12345',
			email='other@coftu.local',
			first_name='Other',
			last_name='User',
			phone='0700000011',
			position='Officer',
		)

	def test_private_event_visible_only_to_owner(self):
		now = timezone.now()
		CalendarEvent.objects.create(
			title='Private Strategy Session',
			start_datetime=now + timedelta(hours=1),
			end_datetime=now + timedelta(hours=2),
			visibility=CalendarEvent.VISIBILITY_PRIVATE,
			created_by=self.owner,
		)
		CalendarEvent.objects.create(
			title='Public Union Briefing',
			start_datetime=now + timedelta(hours=3),
			end_datetime=now + timedelta(hours=4),
			visibility=CalendarEvent.VISIBILITY_PUBLIC,
			created_by=self.owner,
		)

		self.client.login(username='other_user', password='pass12345')
		response = self.client.get(reverse('dashapp:calendar'))
		self.assertContains(response, 'Public Union Briefing')
		self.assertNotContains(response, 'Private Strategy Session')
