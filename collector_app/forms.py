"""
Collector app forms
"""
from django import forms
from user_app.models import Complaint, PickupRequest, CollectionProof


COMPLAINT_STATUS_CHOICES = [
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
]

PICKUP_STATUS_CHOICES = [
    ('accepted', 'Accepted'),
    ('on_the_way', 'On The Way'),
    ('collected', 'Collected'),
    ('completed', 'Completed'),
]


class UpdateComplaintStatusForm(forms.ModelForm):
    """Let collectors update complaint status."""

    status = forms.ChoiceField(
        choices=COMPLAINT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Complaint
        fields = ['status']


class UpdatePickupStatusForm(forms.ModelForm):
    """Let collectors update pickup request status."""

    status = forms.ChoiceField(
        choices=PICKUP_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = PickupRequest
        fields = ['status']


class CollectionProofForm(forms.ModelForm):
    """Upload proof of collection."""

    class Meta:
        model = CollectionProof
        fields = ['photo', 'notes']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any notes about the collection...'
            }),
        }
