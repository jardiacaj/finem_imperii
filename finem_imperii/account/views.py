from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect, render, get_object_or_404

from messaging.models import ServerMOTD


def register_view(request):
    if request.user.is_authenticated():
        return redirect('base:home')
    if request.POST:
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if User.objects.filter(email=email).exists():
            messages.add_message(request, messages.ERROR, "An account with this email address already exists", extra_tags="danger")
            return redirect('base:register')

        if User.objects.filter(username=username).exists():
            messages.add_message(request, messages.ERROR, "An account with this username already exists", extra_tags="danger")
            return redirect('base:register')

        if password != password2:
            messages.add_message(request, messages.ERROR, "Your passwords don't match!", extra_tags="danger")
            return redirect('base:register')

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
                return redirect('base:home')
            else:
                messages.add_message(request, messages.ERROR, "You account is disabled.", extra_tags='danger')
                return redirect('account:login')
        else:
            messages.add_message(request, messages.ERROR, "Your username and/or your password is incorrect.", extra_tags='warning')
            return redirect('account:login')
    else:
        if request.user.is_authenticated():
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
        'server_messages': ServerMOTD.objects.all() if request.user.is_staff else ServerMOTD.objects.filter(draft=False)
    }
    return render(request, 'account/home.html', context=context)
