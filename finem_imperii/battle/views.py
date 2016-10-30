import json

from django.contrib import messages
from django.forms.models import model_to_dict
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect

from battle.models import Battle, BattleTurn, BattleUnit, BattleUnitInTurn, BattleObject, BattleObjectInTurn
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
        'units': own_battle_units
    }
    return render(request, 'battle/setup.html', context=context)


def view_battle(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)

    context = {
        'battle_data': json.dumps(battle.render_for_view())
    }
    return render(request, 'battle/view.html', context=context)


def create_test_battle3(request):
    battle = Battle()
    battle.save()
    battle.start_battle_test()
    for i in range(30):
        print(i)
        battle.do_turn()
    return redirect(battle.get_absolute_url())
