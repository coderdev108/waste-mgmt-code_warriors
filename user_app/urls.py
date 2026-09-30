"""URL patterns for the citizen app."""
from django.urls import path
from user_app import views

urlpatterns = [
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('report/', views.report_issue, name='report_issue'),
    path('pickup/', views.pickup_request, name='pickup_request'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('awareness/', views.awareness, name='awareness'),
    # AI Waste Classification
    path('ai-scan/', views.ai_waste_scan, name='ai_waste_scan'),
    path('ai-scan/save/', views.save_scan_result, name='save_scan_result'),
    # Citizen Feedback & Rating
    path('complaint/<int:pk>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('complaint/<int:pk>/get-feedback/', views.get_feedback, name='get_feedback'),
    # Duplicate Complaint Detection
    path('check-duplicates/', views.check_duplicates, name='check_duplicates'),
    # Image AI / Duplicate Detection
    path('check-image/', views.check_image, name='check_image'),
]
