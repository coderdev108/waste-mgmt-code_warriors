"""
Authentication forms: Registration and Login
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from accounts.models import CustomUser


class CitizenRegistrationForm(UserCreationForm):
    """Form for citizen self-registration."""
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'address', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'citizen'  # Always citizen on public registration
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CollectorRegistrationForm(UserCreationForm):
    """Form for admin to add new collectors."""
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    zone = forms.CharField(max_length=100, required=False, help_text="Assigned collection zone")

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'zone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'collector'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    """Styled login form."""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
        'autofocus': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
