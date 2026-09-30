"""
Collector app views for Smart Waste Management System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from user_app.models import Complaint, PickupRequest, CollectionProof
from collector_app.forms import UpdateComplaintStatusForm, UpdatePickupStatusForm, CollectionProofForm


def collector_required(view_func):
    """Decorator to restrict access to collectors only."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.role == 'collector' or request.user.is_superuser):
            messages.error(request, '⛔ Access denied. Collector account required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@collector_required
def collector_dashboard(request):
    """Collector dashboard showing all active assigned tasks."""
    today = timezone.now().date()

    # All tasks assigned to this collector
    complaints = Complaint.objects.filter(assigned_to=request.user)
    pickups = PickupRequest.objects.filter(assigned_to=request.user)

    # Active complaints
    active_complaints = complaints.exclude(status__in=['resolved', 'rejected']).order_by('-updated_at')
    
    # Active pickups (all active, prioritized by date)
    active_pickups = pickups.exclude(status__in=['completed', 'cancelled']).order_by('preferred_date', 'preferred_time')

    context = {
        'total_assigned': complaints.count() + pickups.count(),
        'pending_complaints': active_complaints.count(),
        'completed_today': complaints.filter(status='resolved').count() + pickups.filter(status='completed').count(),
        'pending_pickups': active_pickups.count(),
        'recent_complaints': active_complaints[:8],
        'todays_pickups': active_pickups[:8],
    }
    return render(request, 'collector_app/dashboard.html', context)


@collector_required
def my_tasks(request):
    """View all tasks (complaints + pickups) assigned to this collector."""
    complaints = Complaint.objects.filter(assigned_to=request.user).order_by('-updated_at')
    pickups = PickupRequest.objects.filter(assigned_to=request.user).order_by('-updated_at')

    status_filter = request.GET.get('status', '')
    task_type = request.GET.get('type', 'complaint')

    if status_filter:
        complaints = complaints.filter(status=status_filter)
        pickups = pickups.filter(status=status_filter)

    return render(request, 'collector_app/tasks.html', {
        'complaints': complaints,
        'pickups': pickups,
        'status_filter': status_filter,
        'task_type': task_type,
    })


@collector_required
def task_detail_complaint(request, pk):
    """View and update a single assigned complaint."""
    complaint = get_object_or_404(Complaint, pk=pk, assigned_to=request.user)
    proofs = complaint.proofs.all()

    # Status update form
    if request.method == 'POST':
        if 'update_status' in request.POST:
            form = UpdateComplaintStatusForm(request.POST, instance=complaint)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Status updated successfully!')
                return redirect('task_detail_complaint', pk=pk)
        elif 'upload_proof' in request.POST:
            proof_form = CollectionProofForm(request.POST, request.FILES)
            if proof_form.is_valid():
                proof = proof_form.save(commit=False)
                proof.complaint = complaint
                proof.collected_by = request.user
                proof.save()
                # Auto-update complaint status to resolved
                complaint.status = 'resolved'
                complaint.save()
                messages.success(request, '✅ Proof uploaded and complaint marked as resolved!')
                return redirect('task_detail_complaint', pk=pk)
    else:
        form = UpdateComplaintStatusForm(instance=complaint)
        proof_form = CollectionProofForm()

    return render(request, 'collector_app/task_detail.html', {
        'task': complaint,
        'task_type': 'complaint',
        'form': form,
        'proof_form': proof_form,
        'proofs': proofs,
    })


@collector_required
def task_detail_pickup(request, pk):
    """View and update a single assigned pickup request."""
    pickup = get_object_or_404(PickupRequest, pk=pk, assigned_to=request.user)
    proofs = pickup.proofs.all()

    if request.method == 'POST':
        if 'update_status' in request.POST:
            form = UpdatePickupStatusForm(request.POST, instance=pickup)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Status updated successfully!')
                return redirect('task_detail_pickup', pk=pk)
        elif 'upload_proof' in request.POST:
            proof_form = CollectionProofForm(request.POST, request.FILES)
            if proof_form.is_valid():
                proof = proof_form.save(commit=False)
                proof.pickup_request = pickup
                proof.collected_by = request.user
                proof.save()
                pickup.status = 'completed'
                pickup.save()
                messages.success(request, '✅ Proof uploaded and pickup marked as completed!')
                return redirect('task_detail_pickup', pk=pk)
    else:
        form = UpdatePickupStatusForm(instance=pickup)
        proof_form = CollectionProofForm()

    return render(request, 'collector_app/task_detail.html', {
        'task': pickup,
        'task_type': 'pickup',
        'form': form,
        'proof_form': proof_form,
        'proofs': proofs,
    })
