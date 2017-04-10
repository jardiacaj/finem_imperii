import json

from django.shortcuts import render, get_object_or_404

from battle.models import Battle
from decorators import inchar_required


@inchar_required
def view_battle(request, battle_id):
    battle = get_object_or_404(Battle, pk=battle_id)

    context = {
        'battle_data': json.dumps(battle.render_for_view())
    }
    return render(request, 'battle/view.html', context=context)
