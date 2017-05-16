from django.shortcuts import render, redirect


def homepage(request):
    if request.user.is_authenticated():
        return redirect('account:home')
    else:
        return render(request, "base/homepage.html")
