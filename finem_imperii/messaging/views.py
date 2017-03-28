from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse

from decorators import inchar_required
from messaging.models import MessageReceiver


@inchar_required
def home(request):
    context = {
        'tab': 'new',
        'receiver_list': request.hero.messagereceiver_set.filter(read=False)
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def compose(request):
    context = {
        'tab': 'compose',
    }
    return render(request, 'messaging/compose.html', context)


@inchar_required
def mark_all_read(request):
    request.hero.unread_messages().all().update(read=True)
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def mark_read(request, receiver_id):
    receiver = get_object_or_404(MessageReceiver, id=receiver_id, character=request.hero)
    receiver.read = not receiver.read
    receiver.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('messaging:home')))


@inchar_required
def mark_favourite(request, receiver_id):
    receiver = get_object_or_404(MessageReceiver, id=receiver_id, character=request.hero)
    receiver.favourite = not receiver.favourite
    receiver.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('messaging:home')))


@inchar_required
def messages_list(request):
    context = {
        'tab': 'all',
        'receiver_list': request.hero.messagereceiver_set.all()
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def favourites_list(request):
    context = {
        'tab': 'favourites',
        'receiver_list': request.hero.messagereceiver_set.filter(favourite=True)
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def sent_list(request):
    context = {
        'tab': 'sent',
        'emssage_list': request.hero.messages_sent
    }
    return render(request, 'messaging/sent_list.html', context)
