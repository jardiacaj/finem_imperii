from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from character.models import Character


def world_blocked(request):
    messages.warning(
        request,
        "{} is undergoing a turn pass. Try again in a few minutes.".format(request.hero.world)
    )
    return redirect('account:home')


def inchar_required(func):
    @login_required
    def inner(*args, **kwargs):
        hero = get_object_or_404(
            Character,
            pk=args[0].session.get('character_id', 0),
            owner_user=args[0].user,
            paused=False
        )
        args[0].hero = hero

        if hero.world.blocked_for_turn:
            return world_blocked(args[0])

        return func(*args, **kwargs)

    return inner
