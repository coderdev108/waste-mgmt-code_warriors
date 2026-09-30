"""URL patterns for the admin panel app."""
from django.urls import path
from admin_app import views
from collector_app import api_views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('complaints/', views.all_complaints, name='all_complaints'),
    path('complaints/<int:pk>/assign/', views.assign_complaint, name='assign_complaint'),
    path('pickups/', views.all_pickups, name='all_pickups'),
    path('pickups/<int:pk>/assign/', views.assign_pickup, name='assign_pickup'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:pk>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('collectors/', views.manage_collectors, name='manage_collectors'),
    path('awareness/', views.awareness_list, name='awareness_list'),
    path('awareness/create/', views.awareness_create, name='awareness_create'),
    path('awareness/<int:pk>/edit/', views.awareness_edit, name='awareness_edit'),
    path('awareness/<int:pk>/delete/', views.awareness_delete, name='awareness_delete'),
    path('hotspot-map/', views.hotspot_map, name='hotspot_map'),
    # Live stats API
    path('api/stats/', api_views.admin_stats_api, name='admin_stats_api'),
]
