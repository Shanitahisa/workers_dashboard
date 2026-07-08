from django.urls import path

from . import views

app_name = 'dashapp'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('action-points/', views.action_point_list, name='action_point_list'),
    path('action-points/create/', views.action_point_create, name='action_point_create'),
    path('action-points/<int:pk>/', views.action_point_detail, name='action_point_detail'),
    path('action-points/<int:pk>/assign/', views.assign_action_point, name='assign_action_point'),
    path('assignments/', views.my_assignments, name='my_assignments'),
    path('assignments/<int:pk>/progress/', views.add_progress_update, name='add_progress_update'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/create/', views.calendar_event_create, name='calendar_event_create'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/<int:pk>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/preferences/', views.notification_preferences, name='notification_preferences'),
]
