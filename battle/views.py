import json

from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect

from battle.battle_renderer import render_battle_for_view
from battle.models import Battle
from decorators import inchar_required


@inchar_required
def info_view(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)

    context = {'battle': battle}

    return render(request, 'battle/info_view.html', context=context)


@inchar_required
def battlefield_view(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)

    if not battle.started:
        return redirect('battle:info', battle_id=battle_id)

    context = {'battle': battle}

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
