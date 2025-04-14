from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from accounts.forms import CustomUserCreationForm


def custom_logout_view(request):
    logout(request)
    return redirect('home')

def forgot_username(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            send_mail(
                'Your Username',
                f'Hello! Your username is: {user.username}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Your username has been sent to your email.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email.')
    return render(request, 'accounts/forgot_username.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    login_form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

    return redirect('dashboard')
  
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')

