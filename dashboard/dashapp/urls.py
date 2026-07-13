from django.urls import path

from . import views

app_name = 'dashapp'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('profile/', views.profile_detail, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('logout/', views.logout_view, name='logout'),
    path('action-points/', views.action_point_list, name='action_point_list'),
    path('action-points/create/', views.action_point_create, name='action_point_create'),
    path('action-points/<int:pk>/', views.action_point_detail, name='action_point_detail'),
    path('action-points/<int:pk>/assign/', views.assign_action_point, name='assign_action_point'),
    path('assignments/', views.my_assignments, name='my_assignments'),
    path('assignments/<int:pk>/progress/', views.add_progress_update, name='add_progress_update'),
    path('assignments/<int:pk>/done/', views.mark_assignment_done, name='mark_assignment_done'),
    path('assignments/<int:pk>/postpone/', views.postpone_assignment, name='postpone_assignment'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/create/', views.calendar_event_create, name='calendar_event_create'),
    path('calendar/<int:pk>/edit/', views.calendar_event_edit, name='calendar_event_edit'),
    path('calendar/<int:pk>/delete/', views.calendar_event_delete, name='calendar_event_delete'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/create/', views.alert_create, name='alert_create'),
    path('alerts/<int:pk>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/preferences/', views.notification_preferences, name='notification_preferences'),
]
