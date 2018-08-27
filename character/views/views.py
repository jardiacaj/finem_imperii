from django.shortcuts import render, get_object_or_404

from character.models import Character
from decorators import inchar_required
from messaging.models import MessageRelationship
from organization.models.capability import Capability
from world.renderer import render_world_for_view


@inchar_required
def character_home(request):
    elections = (
        capability.applying_to.current_election for capability in
    Capability.objects.filter(
            applying_to__current_election__isnull=False,
            type=Capability.ELECT,
            organization__in=request.hero.organization_set.all()
        )
    )

    context = {
        'displayed_object': request.hero,
        'current_elections': elections,
    }
    return render(request, 'character/character_home.html', context=context)


@inchar_required
def character_view(request, character_id):
    character = get_object_or_404(
        Character,
        id=character_id,
        world=request.hero.world
    )
    favourite = MessageRelationship.objects.filter(
        from_character=request.hero,
        to_character=character
    ).exists()
    context = {
        'character': character,
        'favourite': favourite,
        'displayed_object': character,
    }
    return render(request, 'character/view_character.html', context=context)


@inchar_required
def character_view_iframe(request, character_id):
    character = get_object_or_404(
        Character,
        id=character_id,
        world=request.hero.world
    )
    context = {
        'character': character,
        'world_data': render_world_for_view(character.world),
    }
    return render(request,
                  'character/view_character_iframe.html', context)