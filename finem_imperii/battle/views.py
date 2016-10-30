import json

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect

from battle.models import Battle, BattleTurn, BattleUnit, BattleUnitInTurn, BattleObject, BattleObjectInTurn, Order, \
    OrderListElement, BattleCharacter
from decorators import inchar_required


@inchar_required
def setup_view(request, battle_id):
    battle = get_object_or_404(Battle, id=battle_id)
    own_battle_character = request.hero.battlecharacter_set.all() & battle.battlecharacter_set.all()
    if not own_battle_character:
        raise Http404("Not taking part in this battle!")
    own_battle_character = own_battle_character[0]

    own_battle_units = own_battle_character.battleunit_set.all()

    context = {
        'battle': battle,
        'units': own_battle_units,
        'battle_character': own_battle_character
    }
    return render(request, 'battle/setup.html', context=context)


@inchar_required
def ready_view(request, battle_character_id):
    battle_character = get_object_or_404(BattleCharacter, id=battle_character_id)
    if not battle_character.character == request.hero:
        raise Http404("Not taking part in this battle!")
    battle_character.ready = True
    battle_character.save()
    battle_character.battle.check_all_ready()
    return redirect(reverse('battle:setup', kwargs={'battle_id': battle_character.battle.id}))


@inchar_required
def view_battle(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)

    context = {
        'battle_data': json.dumps(battle.render_for_view())
    }
    return render(request, 'battle/view.html', context=context)


@inchar_required
def set_orders(request, battle_unit_id):
    if request.method != "POST":
        raise Http404("Please POST")
    battle_unit = get_object_or_404(BattleUnit, pk=battle_unit_id)
    if battle_unit.owner.character != request.hero:
        raise Http404("Not your unit!")
    battle_unit.orders.clear()
    order = Order(what=request.POST.get("order"))
    order.save()
    ole = OrderListElement(order=order, battle_unit=battle_unit, position=0)
    ole.save()
    battle_unit.starting_x_pos = request.POST.get("x_pos")
    battle_unit.starting_z_pos = request.POST.get("z_pos")
    battle_unit.save()
    return redirect(reverse('battle:setup', kwargs={'battle_id': battle_unit.owner.battle.id}))
