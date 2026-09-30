"""
Register user_app models in Django admin
"""
from django.contrib import admin
from user_app.models import Complaint, PickupRequest, CollectionProof, Awareness, WasteClassification, ComplaintFeedback, CommonIncident


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['title', 'issue_type', 'status', 'reported_by', 'assigned_to', 'created_at']
    list_filter = ['status', 'issue_type']
    search_fields = ['title', 'description', 'location_address']
    list_editable = ['status']


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ['waste_type', 'status', 'requested_by', 'assigned_to', 'preferred_date']
    list_filter = ['status', 'waste_type']
    list_editable = ['status']


@admin.register(CollectionProof)
class CollectionProofAdmin(admin.ModelAdmin):
    list_display = ['collected_by', 'complaint', 'pickup_request', 'created_at']


@admin.register(Awareness)
class AwarenessAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'created_by', 'created_at']
    list_editable = ['is_active']


@admin.register(WasteClassification)
class WasteClassificationAdmin(admin.ModelAdmin):
    list_display = ['scanned_by', 'predicted_category', 'confidence', 'scanned_at']
    list_filter = ['predicted_category']
    readonly_fields = ['scanned_at']


@admin.register(ComplaintFeedback)
class ComplaintFeedbackAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'submitted_by', 'rating', 'created_at']
    list_filter = ['rating']
    readonly_fields = ['created_at']


@admin.register(CommonIncident)
class CommonIncidentAdmin(admin.ModelAdmin):
    list_display = ['id', 'issue_type', 'report_count', 'status', 'location_address', 'created_at']
    list_filter  = ['status', 'issue_type']
    list_editable = ['status']
    search_fields = ['title', 'location_address']
    readonly_fields = ['report_count', 'created_at', 'updated_at']
