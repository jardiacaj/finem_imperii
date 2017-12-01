import json

from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect

from battle.battle_renderer import render_battle_for_view
from battle.models import Battle
from decorators import inchar_required
from unit.models import WorldUnit


@inchar_required
def info_view(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id, tile__world=request.hero.world)
    heros_units = WorldUnit.objects.filter(
        battleunit__in=battle.get_units_in_battle().filter(world_unit__owner_character=request.hero)
    )

    context = {
        'battle': battle,
        'heros_units': heros_units,
    }

    return render(request, 'battle/info_view.html', context=context)


@inchar_required
def battlefield_view(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)
    heros_units = WorldUnit.objects.filter(
        battleunit__in=battle.get_units_in_battle().filter(world_unit__owner_character=request.hero)
    )

    if not battle.started:
        return redirect('battle:info', battle_id=battle_id)

    context = {
        'battle': battle,
        'heros_units': heros_units,
        'hide_sidebar': True
    }

    return render(request, 'battle/battlefield_view.html', context=context)


@inchar_required
def battlefield_view_iframe(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)

    if not battle.started:
        raise Http404()

    context = {
        'battle_data': json.dumps(render_battle_for_view(battle))
    }
    return render(request, 'battle/battlefield_view_iframe.html', context=context)
