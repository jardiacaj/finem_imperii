from django.shortcuts import redirect
from django.urls import reverse

from base.utils import redirect_back
from decorators import inchar_required
from messaging.models import MessageRecipient
from messaging.views.decorators import recipient_required_decorator


@inchar_required
def mark_all_read(request):
    MessageRecipient.objects.filter(
        character=request.hero, read=False).update(read=True)
    return redirect_back(request, reverse('character:character_home'))


@recipient_required_decorator
def mark_read(request, recipient_id):
    request.recipient.read = not request.recipient.read
    request.recipient.save()
    return redirect_back(request, reverse('messaging:home'))


@recipient_required_decorator
def mark_favourite(request, recipient_id):
    request.recipient.favourite = not request.recipient.favourite
    request.recipient.save()
    return redirect_back(request, reverse('messaging:home'))
