from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from base.utils import redirect_back
from battle.models import Order
from decorators import inchar_required
from unit.models import WorldUnit, WorldUnitStatusChangeException


@inchar_required
@require_POST
def status_change(request, unit_id, new_status):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    try:
        unit.change_status(new_status)
    except WorldUnitStatusChangeException as e:
        messages.error(request, str(e), "danger")
    return redirect_back(request, unit.get_absolute_url())


@inchar_required
@require_POST
def battle_settings(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    battle_line = int(request.POST['battle_line'])
    battle_side_pos = int(request.POST['battle_side_pos'])
    if not 0 <= battle_line < 5 or not -5 <= battle_side_pos <= 5:
        raise Http404("Invalid settings")
    battle_orders = request.POST['battle_orders']
    if battle_orders not in [order[0] for order in Order.WHAT_CHOICES]:
        raise Http404("Invalid orders")

    unit.default_battle_orders = Order.objects.create(what=battle_orders)
    unit.battle_side_pos = battle_side_pos
    unit.battle_line = battle_line
    unit.save()

    return redirect_back(request, unit.get_absolute_url())
