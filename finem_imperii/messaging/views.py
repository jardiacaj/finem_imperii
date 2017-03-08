from django.shortcuts import render, redirect
from django.urls.base import reverse

from decorators import inchar_required


@inchar_required
def clear_notifications(request):
    request.hero.unread_notifications().update(read=True)
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def notification_list(request):
    return render(request, 'messaging/notification_list.html')
