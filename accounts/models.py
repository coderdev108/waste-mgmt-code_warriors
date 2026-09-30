"""
Custom User model for Smart Waste Management System
Supports three roles: citizen (user), admin, and collector
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model with role-based access."""

    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('admin', 'Admin'),
        ('collector', 'Collector'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    # For collectors: their assigned zone/area
    zone = models.CharField(max_length=100, blank=True, null=True, help_text="Collector's assigned zone")
    is_approved = models.BooleanField(default=True)  # Admin can deactivate users

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_citizen(self):
        return self.role == 'citizen'

    @property
    def is_admin_user(self):
        return self.role == 'admin'

    @property
    def is_collector(self):
        return self.role == 'collector'
