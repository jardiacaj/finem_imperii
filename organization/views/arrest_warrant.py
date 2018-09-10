from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from base.utils import redirect_back
from character.models import Character, CharacterEvent
from organization.models.capability import Capability
from organization.views.proposal import capability_success
from organization.views.decorator import capability_required_decorator


@require_POST
@capability_required_decorator
def arrest_warrant_capability_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.ARREST_WARRANT)

    target_character = get_object_or_404(
        Character, id=request.POST.get('character_to_imprison_id'))
    if target_character.world != capability.applying_to.world:
        return redirect_back(request, reverse('character:character_home'),
                             error_message="You cannot do that")

    proposal = {'action': 'issue', 'character_id': target_character.id}
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)

@require_POST
@capability_required_decorator
def arrest_warrant_revoke_capability_view(request, capability_id, warrant_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.ARREST_WARRANT)

    warrant = get_object_or_404(
        CharacterEvent,
        id=warrant_id,
        active=True,
        organization=capability.applying_to,
        type=CharacterEvent.ARREST_WARRANT
    )

    proposal = {'action': 'revoke', 'warrant_id': warrant.id}
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)
