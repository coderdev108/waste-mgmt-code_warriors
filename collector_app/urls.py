"""URL patterns for the collector app."""
from django.urls import path
from collector_app import views, api_views

urlpatterns = [
    path('dashboard/', views.collector_dashboard, name='collector_dashboard'),
    path('tasks/', views.my_tasks, name='my_tasks'),
    path('tasks/complaint/<int:pk>/', views.task_detail_complaint, name='task_detail_complaint'),
    path('tasks/pickup/<int:pk>/', views.task_detail_pickup, name='task_detail_pickup'),
    # Real-time API
    path('api/tasks/', api_views.collector_tasks_api, name='collector_tasks_api'),
]
