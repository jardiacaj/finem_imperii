from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from character.models import Character
from organization.models import Capability
from organization.views.capabilities_generics import capability_success
from organization.views.decorator import capability_required_decorator


@require_POST
@capability_required_decorator
def banning_capability_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.BAN)

    character_to_ban = get_object_or_404(
        Character, id=request.POST.get('character_to_ban_id'))
    if character_to_ban not in capability.applying_to.character_members.all():
        messages.error(request, "You cannot do that", "danger")
        return redirect(request.META.get('HTTP_REFERER',
                                         reverse('character:character_home')))

    proposal = {'character_id': character_to_ban.id}
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)
