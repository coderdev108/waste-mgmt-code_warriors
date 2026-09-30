"""
Register accounts models in Django admin
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'zone', 'is_approved', 'is_active']
    list_filter = ['role', 'is_active', 'is_approved']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {'fields': ('role', 'phone', 'address', 'zone', 'profile_photo', 'is_approved')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Profile', {'fields': ('role', 'phone', 'address', 'zone', 'is_approved')}),
    )
