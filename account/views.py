from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from account.user_functions import can_create_character
from messaging.models import ServerMOTD


def register_view(request):
    if request.user.is_authenticated:
        return redirect('account:home')
    if request.POST:
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if User.objects.filter(email=email).exists():
            messages.add_message(
                request,
                messages.ERROR,
                "An account with this email address already exists",
                extra_tags="danger"
            )
            return redirect('account:register')

        if User.objects.filter(username=username).exists():
            messages.add_message(
                request,
                messages.ERROR,
                "An account with this username already exists",
                extra_tags="danger"
            )
            return redirect('account:register')

        if password != password2:
            messages.add_message(request, messages.ERROR, "Your passwords don't match!", extra_tags="danger")
            return redirect('account:register')

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.add_message(request, messages.SUCCESS, "Account created. Please log in.", extra_tags="success")
        return redirect('account:login')

    else:
        return render(request, 'account/register.html')


def login_view(request):
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.add_message(request, messages.SUCCESS, "Login successful.", extra_tags='success')
                return redirect('account:home')
        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Your username and/or your password is incorrect.",
                extra_tags='warning'
            )
            return redirect('account:login')
    else:
        if request.user.is_authenticated:
            return redirect('account:home')
        else:
            return render(request, 'account/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.SUCCESS, "You have been logged out.", extra_tags='success')
    return redirect('base:home')


@login_required
def home(request):
    context = {
        'server_messages': ServerMOTD.objects.all() if request.user.is_staff
                           else ServerMOTD.objects.filter(draft=False),
        'can_create_character': can_create_character(request.user)
    }
    return render(request, 'account/home.html', context=context)
