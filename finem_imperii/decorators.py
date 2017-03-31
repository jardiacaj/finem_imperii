from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from world.models import Character


def inchar_required(func):
    @login_required
    def inner(*args, **kwargs):
        hero = get_object_or_404(
            Character,
            pk=args[0].session.get('character_id', 0),
            owner_user=args[0].user,
        )
        args[0].hero = hero
        return func(*args, **kwargs)

    return inner
