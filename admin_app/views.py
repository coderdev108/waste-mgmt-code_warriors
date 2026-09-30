"""
Admin panel views for Smart Waste Management System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from user_app.models import Complaint, PickupRequest, Awareness
from accounts.models import CustomUser
from admin_app.forms import AssignComplaintForm, AssignPickupForm, AwarenessForm
from accounts.forms import CollectorRegistrationForm
import json


def admin_required(view_func):
    """Decorator to restrict access to admin users only."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, '⛔ Access denied. Admin privileges required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    """Admin dashboard with statistics and Chart.js data."""
    complaints = Complaint.objects.all()
    pickups = PickupRequest.objects.all()
    users = CustomUser.objects.filter(role='citizen')
    collectors = CustomUser.objects.filter(role='collector')

    # Stats for cards
    stats = {
        'total_complaints': complaints.count(),
        'pending_complaints': complaints.filter(status='pending').count(),
        'in_progress_complaints': complaints.filter(status='in_progress').count(),
        'resolved_complaints': complaints.filter(status='resolved').count(),
        'total_pickups': pickups.count(),
        'pending_pickups': pickups.filter(status='pending').count(),
        'total_users': users.count(),
        'total_collectors': collectors.count(),
    }

    # Chart data: complaints by status
    status_labels = ['Pending', 'In Progress', 'Resolved', 'Rejected']
    status_data = [
        complaints.filter(status='pending').count(),
        complaints.filter(status='in_progress').count(),
        complaints.filter(status='resolved').count(),
        complaints.filter(status='rejected').count(),
    ]

    # Chart data: complaints by type
    type_labels = [ct[1] for ct in Complaint.ISSUE_TYPES]
    type_data = [complaints.filter(issue_type=ct[0]).count() for ct in Complaint.ISSUE_TYPES]

    # Recent complaints for quick view
    recent_complaints = complaints.order_by('-created_at')[:10]
    recent_pickups = pickups.order_by('-created_at')[:5]

    # Map data: complaints with location
    map_complaints = complaints.exclude(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    ).values('id', 'title', 'issue_type', 'status', 'latitude', 'longitude', 'location_address')
    map_data = json.dumps(list(map_complaints), default=str)

    context = {
        **stats,
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'type_labels': json.dumps(type_labels),
        'type_data': json.dumps(type_data),
        'recent_complaints': recent_complaints,
        'recent_pickups': recent_pickups,
        'map_data': map_data,
    }
    return render(request, 'admin_app/dashboard.html', context)


@admin_required
def all_complaints(request):
    """View and manage all complaints."""
    complaints = Complaint.objects.select_related('reported_by', 'assigned_to').all()

    # Filtering
    status = request.GET.get('status', '')
    issue_type = request.GET.get('issue_type', '')
    search = request.GET.get('search', '')

    if status:
        complaints = complaints.filter(status=status)
    if issue_type:
        complaints = complaints.filter(issue_type=issue_type)
    if search:
        complaints = complaints.filter(
            Q(title__icontains=search) | Q(description__icontains=search) | Q(location_address__icontains=search)
        )

    context = {
        'complaints': complaints,
        'status_filter': status,
        'issue_type_filter': issue_type,
        'search': search,
        'issue_types': Complaint.ISSUE_TYPES,
        'statuses': Complaint.STATUS_CHOICES,
    }
    return render(request, 'admin_app/complaints.html', context)


@admin_required
def assign_complaint(request, pk):
    """Assign a complaint to a collector and update status."""
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        form = AssignComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.assigned_to and obj.status == 'pending':
                obj.status = 'in_progress'
            obj.save()
            collector_name = obj.assigned_to.get_full_name() if obj.assigned_to else 'None'
            messages.success(request, f'✅ Complaint #{pk} successfully assigned to {collector_name or obj.assigned_to.username}!')
            return redirect('all_complaints')
    else:
        form = AssignComplaintForm(instance=complaint)

    return render(request, 'admin_app/assign_complaint.html', {'form': form, 'complaint': complaint})


@admin_required
def all_pickups(request):
    """View all pickup requests."""
    pickups = PickupRequest.objects.select_related('requested_by', 'assigned_to').all()
    status = request.GET.get('status', '')
    if status:
        pickups = pickups.filter(status=status)

    return render(request, 'admin_app/pickups.html', {
        'pickups': pickups,
        'status_filter': status,
        'statuses': PickupRequest.STATUS_CHOICES,
    })


@admin_required
def assign_pickup(request, pk):
    """Assign a pickup request to a collector."""
    pickup = get_object_or_404(PickupRequest, pk=pk)
    if request.method == 'POST':
        form = AssignPickupForm(request.POST, instance=pickup)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.assigned_to and obj.status == 'pending':
                obj.status = 'accepted'
            obj.save()
            collector_name = obj.assigned_to.get_full_name() if obj.assigned_to else 'None'
            messages.success(request, f'✅ Pickup request #{pk} assigned to {collector_name or obj.assigned_to.username}!')
            return redirect('all_pickups')
    else:
        form = AssignPickupForm(instance=pickup)

    return render(request, 'admin_app/assign_pickup.html', {'form': form, 'pickup': pickup})


@admin_required
def manage_users(request):
    """View and manage citizen accounts."""
    users = CustomUser.objects.filter(role='citizen').order_by('-date_joined')
    return render(request, 'admin_app/users.html', {'users': users})


@admin_required
def toggle_user_status(request, pk):
    """Activate or deactivate a user account."""
    user = get_object_or_404(CustomUser, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'✅ User {user.username} has been {status}.')
    return redirect('manage_users')


@admin_required
def manage_collectors(request):
    """View all collectors and add new ones."""
    collectors = CustomUser.objects.filter(role='collector').order_by('-date_joined')

    if request.method == 'POST':
        form = CollectorRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ New collector account created successfully!')
            return redirect('manage_collectors')
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = CollectorRegistrationForm()

    return render(request, 'admin_app/collectors.html', {
        'collectors': collectors,
        'form': form,
    })


@admin_required
def awareness_list(request):
    """Manage awareness tips and announcements."""
    tips = Awareness.objects.all()
    return render(request, 'admin_app/awareness.html', {'tips': tips})


@admin_required
def awareness_create(request):
    """Create a new awareness tip."""
    if request.method == 'POST':
        form = AwarenessForm(request.POST)
        if form.is_valid():
            tip = form.save(commit=False)
            tip.created_by = request.user
            tip.save()
            messages.success(request, '✅ Awareness tip created!')
            return redirect('awareness_list')
    else:
        form = AwarenessForm()

    return render(request, 'admin_app/awareness_form.html', {'form': form, 'action': 'Create'})


@admin_required
def awareness_edit(request, pk):
    """Edit an existing awareness tip."""
    tip = get_object_or_404(Awareness, pk=pk)
    if request.method == 'POST':
        form = AwarenessForm(request.POST, instance=tip)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Awareness tip updated!')
            return redirect('awareness_list')
    else:
        form = AwarenessForm(instance=tip)

    return render(request, 'admin_app/awareness_form.html', {'form': form, 'action': 'Edit'})


@admin_required
def awareness_delete(request, pk):
    """Delete an awareness tip."""
    tip = get_object_or_404(Awareness, pk=pk)
    tip.delete()
    messages.success(request, '✅ Awareness tip deleted.')
    return redirect('awareness_list')


@admin_required
def hotspot_map(request):
    """Display waste hotspot map."""
    complaints = Complaint.objects.exclude(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    ).values('id', 'title', 'issue_type', 'status', 'latitude', 'longitude', 'location_address')
    map_data = json.dumps(list(complaints), default=str)
    return render(request, 'admin_app/hotspot_map.html', {'map_data': map_data})
