from django.shortcuts import render, redirect

from world.models import World


def homepage(request):
    if request.user.is_authenticated():
        return redirect('account:home')
    else:
        return render(request, "base/homepage.html")


def help_view(request):
    context = {
        'worlds': World.objects.all()
    }
    return render(request, "base/help.html", context=context)
