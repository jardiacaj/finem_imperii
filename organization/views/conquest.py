from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from organization.models import Capability
from organization.views.capabilities_generics import capability_success
from organization.views.decorator import capability_required_decorator
from world.models.events import TileEvent
from world.models.geography import Tile


@require_POST
@capability_required_decorator
def conquest_capability_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.CONQUEST)
    tile_to_conquer = get_object_or_404(
        Tile,id=request.POST.get('tile_to_conquest_id'))

    if request.POST.get('stop'):
        try:
            tile_event = TileEvent.objects.get(
                tile=tile_to_conquer,
                organization=capability.applying_to,
                end_turn__isnull=True
            )
        except TileEvent.DoesNotExist:
            raise Http404
    else:
        if tile_to_conquer not in capability.applying_to.conquestable_tiles():
            raise Http404

    proposal = {
        'tile_id': tile_to_conquer.id,
        'stop': request.POST.get('stop')
    }
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)
