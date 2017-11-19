from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from organization.models import Capability
from organization.views.capabilities_generics import capability_success
from organization.views.decorator import capability_required_decorator
from world.models.geography import Settlement


@require_POST
@capability_required_decorator
def guilds_settings_capability_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.GUILDS)
    settlement = get_object_or_404(
        Settlement, id=request.POST.get('settlement_id'))
    target_option = request.POST.get('option')

    if target_option not in [choice[0] for choice in Settlement.GUILDS_CHOICES]:
        raise Http404("Chosen option not valid")

    if (settlement.tile not in
            capability.applying_to.get_all_controlled_tiles()):
        raise Http404("Settlement not under control")

    proposal = {
        'settlement_id': settlement.id,
        'option': target_option
    }
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)
