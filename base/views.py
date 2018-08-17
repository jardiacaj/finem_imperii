from django.shortcuts import render, redirect

from messaging.models import ServerMOTD


def homepage(request):
    if request.user.is_authenticated:
        return redirect('account:home')
    else:
        context = {
            'server_messages': ServerMOTD.objects.all() if request.user.is_staff
                               else ServerMOTD.objects.filter(draft=False),
        }
        return render(request, "base/homepage.html", context=context)
