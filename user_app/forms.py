"""
Forms for the citizen (user) side of the application
"""
from django import forms
from user_app.models import Complaint, PickupRequest


class ComplaintForm(forms.ModelForm):
    """Form for citizens to report a waste issue."""

    class Meta:
        model = Complaint
        fields = ['title', 'issue_type', 'description', 'photo', 'location_address', 'latitude', 'longitude']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of the issue'
            }),
            'issue_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the issue in detail...'
            }),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'location_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location address or use map pin',
                'id': 'location_address'
            }),
            'latitude': forms.HiddenInput(attrs={'id': 'latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'longitude'}),
        }


class PickupRequestForm(forms.ModelForm):
    """Form for citizens to request waste pickup."""

    class Meta:
        model = PickupRequest
        fields = ['waste_type', 'description', 'preferred_date', 'preferred_time', 'address', 'latitude', 'longitude']
        widgets = {
            'waste_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional details...'
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'preferred_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pickup address',
                'id': 'pickup_address'
            }),
            'latitude': forms.HiddenInput(attrs={'id': 'pickup_lat'}),
            'longitude': forms.HiddenInput(attrs={'id': 'pickup_lng'}),
        }
