from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from base.utils import redirect_back
from decorators import inchar_required
from unit.models import WorldUnit
from world.models.events import TileEvent


@inchar_required
@require_POST
def pay_debt(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        location=request.hero.location
    )  # it is allowed to pay units owned by another character

    owners_debt = unit.get_owners_debt()
    if owners_debt > request.hero.cash:
        return redirect_back(request, unit.get_absolute_url,
                             "You don't have that much money")

    unit.pay_debt(request.hero)
    messages.success(request, "You paid your full debt of {} coins.".format(
        owners_debt
    ))
    return redirect_back(request, unit.get_absolute_url())


@inchar_required
@require_POST
def payment_settings(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )

    if request.POST.get('action') == 'enable' and unit.auto_pay == 0:
        unit.auto_pay = 1
        unit.save()
        messages.success(request, "You enabled auto payment for {}.".format(
            unit
        ))
    elif request.POST.get('action') == 'disable' and unit.auto_pay == 1:
        unit.auto_pay = 0
        unit.save()
        messages.success(request, "You disabled auto payment for {}.".format(
            unit
        ))
    else:
        messages.warning(request, "Invalid action.")

    return redirect_back(request, unit.get_absolute_url())


@inchar_required
@require_POST
def conquest_action(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    tile_event = get_object_or_404(
        TileEvent,
        active=True,
        type=TileEvent.CONQUEST,
        tile=unit.location.tile,
        organization_id=request.POST.get('conqueror_id')
    )
    hours = int(request.POST.get('hours'))
    if unit.status == WorldUnit.NOT_MOBILIZED:
        messages.error(request, "Unit not movilized")
    elif unit.location != request.hero.location:
        messages.error(request, "You must be in the same region to do this.")
    elif not 0 < hours <= request.hero.hours_in_turn_left:
        messages.error(request, "Invalid number of hours")
    elif request.POST.get('action') == "support":
        tile_event.counter += unit.get_fighting_soldiers().count() * hours // (15*24)
        request.hero.hours_in_turn_left -= hours
        request.hero.save()
        tile_event.save()
    elif request.POST.get('action') == "counter":
        tile_event.counter -= unit.get_fighting_soldiers().count() * hours // (15*24)
        request.hero.hours_in_turn_left -= hours
        request.hero.save()
        tile_event.save()
    else:
        messages.error(request, "Invalid action")

    return redirect_back(request, unit.get_absolute_url())


@inchar_required
def disband(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    unit.disband()
    messages.success(request, 'Your unit has been disbanded.', 'success')
    return redirect(reverse('character:character_home'))


@inchar_required
def rename(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    if request.POST.get('name'):
        unit.name = request.POST.get('name')
        unit.save()
    return redirect_back(request, unit.get_absolute_url())
