"""
Authentication views: Login, Logout, Register, Role-based redirect
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.forms import CitizenRegistrationForm, CustomLoginForm


def login_view(request):
    """Custom login view that redirects based on user role."""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}! 👋')
            return redirect_by_role(user)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Public registration for citizens only."""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.first_name or user.username}! 🌿')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CitizenRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """Logout and redirect to login page."""
    logout(request)
    messages.info(request, 'You have been logged out. See you soon! 👋')
    return redirect('login')


@login_required
def role_redirect(request):
    """Redirect authenticated users to their role-specific dashboard."""
    return redirect_by_role(request.user)


def redirect_by_role(user):
    """Helper: return redirect response based on user role."""
    if user.role == 'admin' or user.is_superuser:
        return redirect('admin_dashboard')
    elif user.role == 'collector':
        return redirect('collector_dashboard')
    else:
        return redirect('user_dashboard')
