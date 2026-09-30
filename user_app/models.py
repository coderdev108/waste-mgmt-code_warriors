"""
Core models: Complaint, PickupRequest, CollectionProof, Awareness,
             WasteClassification, ComplaintFeedback, CommonIncident
All shared across apps — lives in user_app as the primary data app
"""
import math
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


# ── Haversine distance (meters) between two lat/lng points ────────────────
def _haversine_m(lat1, lng1, lat2, lng2):
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlam = math.radians(float(lng2) - float(lng1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class CommonIncident(models.Model):
    """
    A grouped incident that aggregates duplicate complaints
    reported about the same garbage pile / location.
    Created automatically when 2+ complaints match within RADIUS_M.
    """
    RADIUS_M = 500  # metres — complaints within this radius are considered same spot

    ISSUE_TYPES = [
        ('overflowing_bin', 'Overflowing Bin'),
        ('garbage_on_road', 'Garbage on Road'),
        ('missed_collection', 'Missed Collection'),
        ('illegal_dumping', 'Illegal Dumping'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    issue_type    = models.CharField(max_length=30, choices=ISSUE_TYPES)
    title         = models.CharField(max_length=200)
    latitude      = models.DecimalField(max_digits=10, decimal_places=7)
    longitude     = models.DecimalField(max_digits=10, decimal_places=7)
    location_address = models.CharField(max_length=300, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    report_count  = models.PositiveIntegerField(default=1)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-report_count', '-created_at']

    def __str__(self):
        return f"Incident #{self.pk} — {self.get_issue_type_display()} ({self.report_count} reports)"

    @classmethod
    def find_nearby(cls, lat, lng, issue_type, radius_m=None):
        """Return open incidents within radius_m of (lat, lng) with same issue_type."""
        if radius_m is None:
            radius_m = cls.RADIUS_M
        candidates = cls.objects.filter(
            issue_type=issue_type,
            status__in=['open', 'in_progress'],
        )
        nearby = []
        for inc in candidates:
            dist = _haversine_m(lat, lng, inc.latitude, inc.longitude)
            if dist <= radius_m:
                nearby.append((dist, inc))
        nearby.sort(key=lambda x: x[0])
        return [inc for _, inc in nearby]


class Complaint(models.Model):
    """Waste complaints reported by citizens."""

    ISSUE_TYPES = [
        ('overflowing_bin', 'Overflowing Bin'),
        ('garbage_on_road', 'Garbage on Road'),
        ('missed_collection', 'Missed Collection'),
        ('illegal_dumping', 'Illegal Dumping'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    issue_type = models.CharField(max_length=30, choices=ISSUE_TYPES, default='other')
    description = models.TextField()
    photo = models.ImageField(upload_to='complaints/', blank=True, null=True)
    image_hash = models.CharField(max_length=64, blank=True, db_index=True)  # MD5 for dup detection
    # Location fields
    location_address = models.CharField(max_length=300, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    # Relationships
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints_reported'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='complaints_assigned'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    # Duplicate detection — link to a shared incident (set on save)
    incident = models.ForeignKey(
        'CommonIncident',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='complaints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def get_status_badge(self):
        """Return Bootstrap badge class for status."""
        badges = {
            'pending': 'warning',
            'in_progress': 'info',
            'resolved': 'success',
            'rejected': 'danger',
        }
        return badges.get(self.status, 'secondary')


class PickupRequest(models.Model):
    """Scheduled waste pickup requests from citizens."""

    WASTE_TYPES = [
        ('general', 'General Waste'),
        ('recyclable', 'Recyclable (Paper/Plastic/Metal)'),
        ('organic', 'Organic / Food Waste'),
        ('hazardous', 'Hazardous (Batteries/Chemicals)'),
        ('e_waste', 'E-Waste (Electronics)'),
        ('bulk', 'Bulk / Furniture'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('on_the_way', 'On The Way'),
        ('collected', 'Collected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    waste_type = models.CharField(max_length=30, choices=WASTE_TYPES)
    description = models.TextField(blank=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pickup_requests'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pickups_assigned'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_waste_type_display()} - {self.requested_by.username}"

    def get_status_badge(self):
        badges = {
            'pending': 'warning',
            'accepted': 'info',
            'on_the_way': 'primary',
            'collected': 'success',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return badges.get(self.status, 'secondary')


class CollectionProof(models.Model):
    """Proof of collection uploaded by collectors."""

    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE,
        related_name='proofs', null=True, blank=True
    )
    pickup_request = models.ForeignKey(
        PickupRequest, on_delete=models.CASCADE,
        related_name='proofs', null=True, blank=True
    )
    photo = models.ImageField(upload_to='proofs/')
    notes = models.TextField(blank=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='proofs_uploaded'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proof by {self.collected_by.username} at {self.created_at.strftime('%Y-%m-%d')}"


class Awareness(models.Model):
    """Eco-awareness tips and announcements from admin."""

    CATEGORY_CHOICES = [
        ('tip', 'Waste Tip'),
        ('announcement', 'Announcement'),
        ('recycling', 'Recycling Guide'),
        ('composting', 'Composting Guide'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tip')
    content = models.TextField()
    icon = models.CharField(max_length=50, default='♻️')  # Emoji icon
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class WasteClassification(models.Model):
    """AI-classified waste scan results uploaded by citizens."""

    WASTE_CATEGORIES = [
        ('wet', 'Wet Waste'),
        ('dry', 'Dry Waste'),
        ('plastic', 'Plastic'),
        ('e_waste', 'E-Waste'),
        ('hazardous', 'Hazardous Waste'),
        ('unknown', 'Unknown'),
    ]

    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='waste_scans'
    )
    image = models.ImageField(upload_to='ai_scans/')
    predicted_category = models.CharField(
        max_length=20, choices=WASTE_CATEGORIES, default='unknown'
    )
    confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    disposal_tip = models.TextField(blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        return f"{self.get_predicted_category_display()} — {self.scanned_by.username} ({self.confidence:.0%})"


class ComplaintFeedback(models.Model):
    """Citizen rating and feedback after a complaint is resolved."""

    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks_given'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Complaint #{self.complaint_id} — {self.rating}★"
