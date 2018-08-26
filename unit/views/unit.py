from django.shortcuts import get_object_or_404, render

from decorators import inchar_required
from unit.models import WorldUnit
from world.models.events import TileEvent


@inchar_required
def unit_view(request, unit_id):
    unit = get_object_or_404(WorldUnit, id=unit_id)
    context = {
        'unit': unit,
        'origins': unit.soldier.origin_distribution(),
        'conquests': TileEvent.objects.filter(
            tile=unit.location.tile,
            type=TileEvent.CONQUEST,
            active=True
        ),
        'displayed_object': unit,
    }
    return render(request, 'unit/view_unit.html', context)