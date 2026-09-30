"""
Admin panel forms
"""
from django import forms
from user_app.models import Complaint, PickupRequest, Awareness
from accounts.models import CustomUser


class AssignComplaintForm(forms.ModelForm):
    """Assign a complaint to a collector."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show collector users in the dropdown
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='collector', is_active=True)
        self.fields['assigned_to'].empty_label = "-- Select Collector --"
        self.fields['assigned_to'].widget.attrs['class'] = 'form-select'
        self.fields['status'].widget.attrs['class'] = 'form-select'
        self.fields['admin_notes'].widget.attrs['class'] = 'form-control'
        self.fields['admin_notes'].widget.attrs['rows'] = 3

    class Meta:
        model = Complaint
        fields = ['assigned_to', 'status', 'admin_notes']


class AssignPickupForm(forms.ModelForm):
    """Assign a pickup request to a collector."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='collector', is_active=True)
        self.fields['assigned_to'].empty_label = "-- Select Collector --"
        self.fields['assigned_to'].widget.attrs['class'] = 'form-select'
        self.fields['status'].widget.attrs['class'] = 'form-select'

    class Meta:
        model = PickupRequest
        fields = ['assigned_to', 'status']


class AwarenessForm(forms.ModelForm):
    """Create/edit awareness tips."""

    class Meta:
        model = Awareness
        fields = ['title', 'category', 'icon', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '♻️'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
