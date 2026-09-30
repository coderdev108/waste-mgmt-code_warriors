"""
Simple JSON API views for real-time polling
No external packages needed - pure Django
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from user_app.models import Complaint, PickupRequest


@login_required
def collector_tasks_api(request):
    """
    Returns JSON of all tasks assigned to the logged-in collector.
    Called every 10s by the collector dashboard JS for real-time updates.
    """
    if request.user.role not in ['collector'] and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    complaints = Complaint.objects.filter(
        assigned_to=request.user
    ).exclude(status__in=['resolved', 'rejected']).values(
        'id', 'title', 'issue_type', 'status', 'location_address',
        'created_at', 'updated_at'
    )

    pickups = PickupRequest.objects.filter(
        assigned_to=request.user
    ).exclude(status__in=['completed', 'cancelled']).values(
        'id', 'waste_type', 'status', 'address',
        'preferred_date', 'preferred_time', 'created_at'
    )

    data = {
        'complaints': list(complaints),
        'pickups': list(pickups),
        'complaint_count': complaints.count(),
        'pickup_count': pickups.count(),
        'total': complaints.count() + pickups.count(),
        'timestamp': timezone.now().isoformat(),
    }
    return JsonResponse(data, safe=False)


@login_required
def citizen_complaint_status_api(request):
    """
    Returns JSON of citizen's own complaints with current status.
    Called every 15s by citizen my-complaints page.
    """
    if request.user.role not in ['citizen'] and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    complaints = Complaint.objects.filter(
        reported_by=request.user
    ).values('id', 'title', 'status', 'updated_at', 'assigned_to__username')

    pickups = PickupRequest.objects.filter(
        requested_by=request.user
    ).values('id', 'waste_type', 'status', 'preferred_date', 'updated_at')

    return JsonResponse({
        'complaints': list(complaints),
        'pickups': list(pickups),
        'timestamp': timezone.now().isoformat(),
    }, safe=False)


@login_required
def admin_stats_api(request):
    """
    Returns live stats for the admin dashboard cards.
    Called every 20s by admin dashboard.
    """
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    complaints = Complaint.objects.all()
    pickups = PickupRequest.objects.all()

    return JsonResponse({
        'total_complaints': complaints.count(),
        'pending': complaints.filter(status='pending').count(),
        'in_progress': complaints.filter(status='in_progress').count(),
        'resolved': complaints.filter(status='resolved').count(),
        'pending_pickups': pickups.filter(status='pending').count(),
        'timestamp': timezone.now().isoformat(),
    })
