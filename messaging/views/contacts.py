from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from base.utils import redirect_back
from character.models import Character
from decorators import inchar_required
from messaging.models import MessageRelationship


@inchar_required
def add_contact(request, character_id):
    target_character = get_object_or_404(
        Character, id=character_id, world=request.hero.world)
    created = MessageRelationship.objects.get_or_create(
        from_character=request.hero, to_character=target_character)[1]
    if created:
        messages.success(request, "Character added to contacts", "success")
    return redirect_back(request, reverse('character:character_home'))


@inchar_required
def remove_contact(request, character_id):
    target_character = get_object_or_404(
        Character, id=character_id, world=request.hero.world)
    try:
        target_relationship = MessageRelationship.objects.get(
            from_character=request.hero, to_character=target_character)
        target_relationship.delete()
        messages.success(request, "Character removed contacts", "success")
    except MessageRelationship.DoesNotExist:
        pass
    return redirect_back(request, reverse('character:character_home'))
