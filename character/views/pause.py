from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from character.models import Character


@login_required
@require_POST
def pause(request):
    character = get_object_or_404(
        Character,
        pk=request.POST.get('character_id'),
        owner_user=request.user
    )
    if character.can_pause():
        character.pause()
        messages.success(
            request,
            "{} has been paused.".format(character),
            "success"
        )
    else:
        messages.error(
            request,
            "{} can't be paused.".format(character),
            "danger"
        )
    return redirect('account:home')


@login_required
@require_POST
def unpause(request):
    character = get_object_or_404(
        Character,
        pk=request.POST.get('character_id'),
        owner_user=request.user
    )
    if character.can_unpause():
        character.unpause()
        messages.success(
            request,
            "{} has been unpaused.".format(character),
            "success"
        )
    else:
        messages.error(
            request,
            "{} can't be unpaused.".format(character),
            "danger"
        )
    return redirect('account:home')