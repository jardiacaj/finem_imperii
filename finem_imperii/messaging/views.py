from django.shortcuts import render, redirect
from django.urls.base import reverse

from decorators import inchar_required


@inchar_required
def home(request):
    return render(request, 'messaging/home.html')


@inchar_required
def mark_all_read(request):
    request.hero.unread_messages().all().update(read=True)
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def messages_list(request):
    return render(request, 'messaging/messages_list.html')
