from django.shortcuts import get_object_or_404

from decorators import inchar_required
from messaging.models import MessageRecipient


def recipient_required_decorator(func):
    @inchar_required
    def inner(*args, **kwargs):
        recipient_id = kwargs.get('recipient_id')
        args[0].recipient = get_object_or_404(
            MessageRecipient, id=recipient_id, character=args[0].hero)
        return func(*args, **kwargs)
    return inner
