from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from character.models import Character
from organization.models.capability import Capability
from organization.views.proposal import capability_success
from organization.views.decorator import capability_required_decorator


@require_POST
@capability_required_decorator
def heir_capability_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.HEIR)

    first_heir_id = request.POST.get('first_heir')
    second_heir_id = request.POST.get('second_heir')

    try:
        first_heir = Character.objects.get(id=first_heir_id)
    except Character.DoesNotExist:
        first_heir = None

    try:
        second_heir = Character.objects.get(id=second_heir_id)
    except Character.DoesNotExist:
        second_heir = None

    if (
            first_heir not in capability.applying_to.get_heir_candidates()
            or
            first_heir == capability.applying_to.get_position_occupier()
    ):
        messages.error(request, "Invalid first heir", "danger")
        return redirect(capability.get_absolute_url())

    if (
            second_heir not in capability.applying_to.get_heir_candidates()
            or
            second_heir == capability.applying_to.get_position_occupier()
    ) and second_heir is not None:
        messages.error(request, "Invalid second heir", "danger")
        return redirect(capability.get_absolute_url())

    proposal = {
        'first_heir': first_heir.id,
        'second_heir': second_heir.id if second_heir is not None else 0
    }

    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)
