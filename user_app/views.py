"""
Citizen (User) views for Smart Waste Management System
"""
import json
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from user_app.models import (
    Complaint, PickupRequest, Awareness, WasteClassification,
    ComplaintFeedback, CommonIncident, _haversine_m
)
from user_app.forms import ComplaintForm, PickupRequestForm
from user_app.ai_image_detector import analyze_image_authenticity


def citizen_required(view_func):
    """Decorator to restrict access to citizens only."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['citizen'] and not request.user.is_superuser:
            if request.user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('collector_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@citizen_required
def user_dashboard(request):
    """Citizen dashboard showing personal stats."""
    complaints = Complaint.objects.filter(reported_by=request.user)
    pickups = PickupRequest.objects.filter(requested_by=request.user)

    context = {
        'total_complaints': complaints.count(),
        'pending_complaints': complaints.filter(status='pending').count(),
        'in_progress_complaints': complaints.filter(status='in_progress').count(),
        'resolved_complaints': complaints.filter(status='resolved').count(),
        'recent_complaints': complaints[:5],
        'recent_pickups': pickups[:3],
        'pending_pickups': pickups.filter(status__in=['pending', 'accepted']).count(),
    }
    return render(request, 'user_app/dashboard.html', context)


@citizen_required
def report_issue(request):
    """Report a new waste issue with photo and location.

    On POST:
    - Checks for existing CommonIncident within 500m for same issue_type
    - If found  → links the new complaint to that incident, increments report_count
    - If not    → creates a brand-new CommonIncident (seeded from this complaint)
    """
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.reported_by = request.user

            # ── Image duplicate / AI check ──────────────────────────
            photo_file = request.FILES.get('photo')
            if photo_file:
                photo_file.seek(0)
                img_hash = hashlib.md5(photo_file.read()).hexdigest()
                photo_file.seek(0)

                # 1. Block exact same photo
                if Complaint.objects.filter(image_hash=img_hash).exists():
                    messages.error(
                        request,
                        '🚫 Duplicate Photo Blocked: This exact photo has already been uploaded in a previous complaint. '
                        'Please upload a new, original photo taken at the location.'
                    )
                    return render(request, 'user_app/report_issue.html', {'form': form})

                # 2. Block AI-generated / synthetic photo
                ai_analysis = analyze_image_authenticity(photo_file)
                if ai_analysis.get('is_ai'):
                    reasons_str = "; ".join(ai_analysis.get('reasons', [])) or 'Synthetic generation markers detected'
                    messages.error(
                        request,
                        f'🤖 AI-Generated Photo Blocked: The system detected this image is AI-generated or synthetic '
                        f'({reasons_str}). Only real photos taken at the waste site are accepted.'
                    )
                    return render(request, 'user_app/report_issue.html', {'form': form})

                complaint.image_hash = img_hash

            lat   = complaint.latitude
            lng   = complaint.longitude
            itype = complaint.issue_type

            if lat and lng:
                # ── Location duplicate grouping ──
                nearby = CommonIncident.find_nearby(lat, lng, itype)
                if nearby:
                    incident = nearby[0]
                    incident.report_count += 1
                    incident.save(update_fields=['report_count', 'updated_at'])
                else:
                    incident = CommonIncident.objects.create(
                        issue_type=itype,
                        title=complaint.title,
                        latitude=lat,
                        longitude=lng,
                        location_address=complaint.location_address,
                    )
                complaint.incident = incident

            complaint.save()

            if complaint.incident and complaint.incident.report_count > 1:
                messages.success(
                    request,
                    f'⚠️ Duplicate detected! • Your complaint has been linked to an existing incident '
                    f'with <strong>{complaint.incident.report_count} reports</strong> about the same issue. '
                    f'This will be treated as a <strong>high-priority</strong> case.'
                )
            else:
                messages.success(request, '✅ Your complaint has been submitted successfully! We\'ll look into it.')

            return redirect('my_complaints')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = ComplaintForm()

    return render(request, 'user_app/report_issue.html', {'form': form})


@citizen_required
def pickup_request(request):
    """Request a scheduled waste pickup."""
    if request.method == 'POST':
        form = PickupRequestForm(request.POST)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.requested_by = request.user
            pickup.save()
            messages.success(request, '✅ Pickup request submitted! We will confirm your schedule soon.')
            return redirect('my_complaints')
        else:
            messages.error(request, 'Please fill all required fields correctly.')
    else:
        form = PickupRequestForm()

    return render(request, 'user_app/pickup_request.html', {'form': form})


@citizen_required
def my_complaints(request):
    """View all complaints and pickup requests by this citizen."""
    complaints = Complaint.objects.filter(reported_by=request.user)
    pickups = PickupRequest.objects.filter(requested_by=request.user)

    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    return render(request, 'user_app/my_complaints.html', {
        'complaints': complaints,
        'pickups': pickups,
        'status_filter': status_filter,
    })


@citizen_required
def complaint_detail(request, pk):
    """View a single complaint with full timeline."""
    complaint = get_object_or_404(Complaint, pk=pk, reported_by=request.user)
    proofs = complaint.proofs.all()
    return render(request, 'user_app/complaint_detail.html', {
        'complaint': complaint,
        'proofs': proofs,
    })


@citizen_required
def awareness(request):
    """Eco-awareness tips and announcements."""
    tips = Awareness.objects.filter(is_active=True)
    return render(request, 'user_app/awareness.html', {'tips': tips})


@citizen_required
def ai_waste_scan(request):
    """AI Waste Classification page — client-side ML via TensorFlow.js."""
    recent_scans = WasteClassification.objects.filter(scanned_by=request.user)[:5]
    return render(request, 'user_app/ai_waste_scan.html', {'recent_scans': recent_scans})


@require_POST
@citizen_required
def save_scan_result(request):
    """AJAX endpoint: save the AI scan result sent from the frontend."""
    try:
        # Image file from form
        image_file = request.FILES.get('image')
        category = request.POST.get('category', 'unknown')
        confidence = float(request.POST.get('confidence', 0))
        disposal_tip = request.POST.get('disposal_tip', '')

        scan = WasteClassification.objects.create(
            scanned_by=request.user,
            image=image_file,
            predicted_category=category,
            confidence=confidence,
            disposal_tip=disposal_tip,
        )
        return JsonResponse({'status': 'ok', 'scan_id': scan.pk})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@citizen_required
def submit_feedback(request, pk):
    """Submit star rating + comment after a complaint is resolved."""
    complaint = get_object_or_404(Complaint, pk=pk, reported_by=request.user, status='resolved')

    # Prevent duplicate feedback
    if hasattr(complaint, 'feedback'):
        return JsonResponse({'status': 'error', 'message': 'Feedback already submitted.'}, status=400)

    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()
        if not (1 <= rating <= 5):
            raise ValueError('Invalid rating')

        ComplaintFeedback.objects.create(
            complaint=complaint,
            submitted_by=request.user,
            rating=rating,
            comment=comment,
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@citizen_required
def get_feedback(request, pk):
    """Return existing feedback for a complaint (JSON)."""
    complaint = get_object_or_404(Complaint, pk=pk, reported_by=request.user)
    try:
        fb = complaint.feedback
        return JsonResponse({'rating': fb.rating, 'comment': fb.comment})
    except ComplaintFeedback.DoesNotExist:
        return JsonResponse({'rating': None})


@citizen_required
def check_duplicates(request):
    """
    AJAX GET endpoint — called live while citizen fills the report form.
    Checks for open incidents + individual complaints nearby.
    Returns JSON with matching incidents and individual complaints.
    """
    try:
        lat       = float(request.GET.get('lat', 0))
        lng       = float(request.GET.get('lng', 0))
        itype     = request.GET.get('issue_type', '')
        radius_m  = int(request.GET.get('radius', CommonIncident.RADIUS_M))
    except (ValueError, TypeError):
        return JsonResponse({'incidents': [], 'complaints': []})

    if not lat or not lng or not itype:
        return JsonResponse({'incidents': [], 'complaints': []})

    # ── Nearby incidents ──
    nearby_incidents = CommonIncident.find_nearby(lat, lng, itype, radius_m)
    incidents_data = [
        {
            'id':            inc.pk,
            'report_count':  inc.report_count,
            'status':        inc.get_status_display(),
            'location':      inc.location_address,
            'distance_m':    round(_haversine_m(lat, lng, inc.latitude, inc.longitude)),
        }
        for inc in nearby_incidents
    ]

    # ── Recent individual complaints within radius (any reporter, last 30 days) ──
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=30)
    open_complaints = Complaint.objects.filter(
        issue_type=itype,
        status__in=['pending', 'in_progress'],
        created_at__gte=cutoff,
        latitude__isnull=False,
        longitude__isnull=False,
    ).exclude(reported_by=request.user).values(
        'pk', 'title', 'location_address', 'latitude', 'longitude', 'created_at', 'status'
    )

    complaints_data = []
    for c in open_complaints:
        dist = _haversine_m(lat, lng, c['latitude'], c['longitude'])
        if dist <= radius_m:
            complaints_data.append({
                'id':         c['pk'],
                'title':      c['title'],
                'location':   c['location_address'],
                'distance_m': round(dist),
                'status':     c['status'],
                'date':       c['created_at'].strftime('%d %b %Y'),
            })
    complaints_data.sort(key=lambda x: x['distance_m'])

    return JsonResponse({
        'incidents':  incidents_data,
        'complaints': complaints_data[:6],
    })


@require_POST
@citizen_required
def check_image(request):
    """
    AJAX POST — receives image file, returns:
      {
        duplicate: bool,
        hash: str,
        is_ai: bool,
        is_suspicious: bool,
        confidence: float,
        score: int,
        reasons: list[str]
      }
    Frontend uses this to warn and block before final submit.
    """
    image = request.FILES.get('image')
    if not image:
        return JsonResponse({
            'duplicate': False,
            'hash': '',
            'is_ai': False,
            'is_suspicious': False,
            'confidence': 0.0,
            'score': 0,
            'reasons': []
        })

    image.seek(0)
    img_hash = hashlib.md5(image.read()).hexdigest()
    image.seek(0)
    duplicate = Complaint.objects.filter(image_hash=img_hash).exists()

    # AI Authenticity Detection
    ai_result = analyze_image_authenticity(image)

    return JsonResponse({
        'duplicate': duplicate,
        'hash': img_hash,
        'is_ai': ai_result.get('is_ai', False),
        'is_suspicious': ai_result.get('is_suspicious', False),
        'confidence': ai_result.get('confidence', 0.0),
        'score': ai_result.get('score', 0),
        'reasons': ai_result.get('reasons', []),
        'dimensions': ai_result.get('dimensions', ''),
    })

