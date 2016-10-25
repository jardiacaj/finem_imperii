import json

from django.forms.models import model_to_dict
from django.shortcuts import render

from battle.models import Battle, BattleTurn, BattleUnit, BattleUnitInTurn, BattleObject, BattleObjectInTurn
from decorators import inchar_required


@inchar_required
def setup_view(request):
    return render(request, 'battle/setup.html')


def test_view(request):
    battle = Battle()
    turn = BattleTurn(battle=battle, num=0)
    turn2 = BattleTurn(battle=battle, num=1)
    turn3 = BattleTurn(battle=battle, num=2)

    unit1 = BattleUnit(battle=battle)
    battle_unit1_in_turn1 = BattleUnitInTurn(battle_unit=unit1, battle_turn=turn, x_pos=50, z_pos=0)
    battle_unit1_in_turn2 = BattleUnitInTurn(battle_unit=unit1, battle_turn=turn2, x_pos=50, z_pos=1)
    battle_unit1_in_turn3 = BattleUnitInTurn(battle_unit=unit1, battle_turn=turn3, x_pos=50, z_pos=3)

    unit2 = BattleUnit(battle=battle)
    battle_unit2_in_turn1 = BattleUnitInTurn(battle_unit=unit2, battle_turn=turn, x_pos=50, z_pos=99)
    battle_unit2_in_turn2 = BattleUnitInTurn(battle_unit=unit2, battle_turn=turn2, x_pos=50, z_pos=98)
    battle_unit2_in_turn3 = BattleUnitInTurn(battle_unit=unit2, battle_turn=turn3, x_pos=50, z_pos=97)

    unit3 = BattleUnit(battle=battle)
    battle_unit3_in_turn1 = BattleUnitInTurn(battle_unit=unit3, battle_turn=turn, x_pos=48, z_pos=99)
    battle_unit3_in_turn2 = BattleUnitInTurn(battle_unit=unit3, battle_turn=turn2, x_pos=48, z_pos=98)
    battle_unit3_in_turn3 = BattleUnitInTurn(battle_unit=unit3, battle_turn=turn3, x_pos=48, z_pos=96)
    
    object1 = BattleObject(battle=battle)
    object1_in_turn1 = BattleObjectInTurn(battle_object=object1, battle_turn=turn, x_pos=49, z_pos=98)
    object1_in_turn2 = BattleObjectInTurn(battle_object=object1, battle_turn=turn2, x_pos=49, z_pos=98)
    object1_in_turn3 = BattleObjectInTurn(battle_object=object1, battle_turn=turn3, x_pos=49, z_pos=98)
    
    object2 = BattleObject(battle=battle)
    object2_in_turn1 = BattleObjectInTurn(battle_object=object2, battle_turn=turn, x_pos=50, z_pos=98)
    object2_in_turn2 = BattleObjectInTurn(battle_object=object2, battle_turn=turn2, x_pos=50, z_pos=98)
    object2_in_turn3 = BattleObjectInTurn(battle_object=object2, battle_turn=turn3, x_pos=50, z_pos=98)
    
    object3 = BattleObject(battle=battle)
    object3_in_turn1 = BattleObjectInTurn(battle_object=object3, battle_turn=turn, x_pos=51, z_pos=98)
    object3_in_turn2 = BattleObjectInTurn(battle_object=object3, battle_turn=turn2, x_pos=51, z_pos=98)
    object3_in_turn3 = BattleObjectInTurn(battle_object=object3, battle_turn=turn3, x_pos=51, z_pos=98)

    units_data = [
        {
            'turn_data': [model_to_dict(battle_unit1_in_turn1), model_to_dict(battle_unit1_in_turn2), model_to_dict(battle_unit1_in_turn3)]
        },
        {
            'turn_data': [model_to_dict(battle_unit2_in_turn1), model_to_dict(battle_unit2_in_turn2), model_to_dict(battle_unit2_in_turn3)]
        },
        {
            'turn_data': [model_to_dict(battle_unit3_in_turn1), model_to_dict(battle_unit3_in_turn2), model_to_dict(battle_unit3_in_turn3)]
        },
    ]

    objects_data = [
        {
            'turn_data': [model_to_dict(object1_in_turn1), model_to_dict(object1_in_turn2), model_to_dict(object1_in_turn3)]
        },
        {
            'turn_data': [model_to_dict(object2_in_turn1), model_to_dict(object2_in_turn2), model_to_dict(object2_in_turn3)]
        },
        {
            'turn_data': [model_to_dict(object3_in_turn1), model_to_dict(object3_in_turn2), model_to_dict(object3_in_turn3)]
        },
    ]

    context = {
        'battle_data': json.dumps(
            {
                'heightmap': [0]*100,
                'unit_data': units_data,
                'turn_count': 3,
                'object_data': objects_data,
            }
        )
    }

    return render(request, 'battle/test.html', context=context)


def create_test_battle(request):

    battle = Battle()
    battle.save()
    turn = BattleTurn(battle=battle, num=0)
    turn.save()
    turn2 = BattleTurn(battle=battle, num=1)
    turn2.save()
    turn3 = BattleTurn(battle=battle, num=2)
    turn3.save()

    unit1 = BattleUnit(battle=battle)
    unit1.save()
    battle_unit1_in_turn1 = BattleUnitInTurn(battle_unit=unit1, battle_turn=turn, x_pos=50, z_pos=0)
    battle_unit1_in_turn2 = BattleUnitInTurn(battle_unit=unit1, battle_turn=turn2, x_pos=50, z_pos=1)
    battle_unit1_in_turn3 = BattleUnitInTurn(battle_unit=unit1, battle_turn=turn3, x_pos=50, z_pos=3)
    battle_unit1_in_turn1.save()
    battle_unit1_in_turn2.save()
    battle_unit1_in_turn3.save()

    unit2 = BattleUnit(battle=battle)
    unit2.save()
    battle_unit2_in_turn1 = BattleUnitInTurn(battle_unit=unit2, battle_turn=turn, x_pos=50, z_pos=99)
    battle_unit2_in_turn2 = BattleUnitInTurn(battle_unit=unit2, battle_turn=turn2, x_pos=50, z_pos=98)
    battle_unit2_in_turn3 = BattleUnitInTurn(battle_unit=unit2, battle_turn=turn3, x_pos=50, z_pos=97)
    battle_unit2_in_turn1.save()
    battle_unit2_in_turn2.save()
    battle_unit2_in_turn3.save()

    unit3 = BattleUnit(battle=battle)
    unit3.save()
    battle_unit3_in_turn1 = BattleUnitInTurn(battle_unit=unit3, battle_turn=turn, x_pos=48, z_pos=99)
    battle_unit3_in_turn2 = BattleUnitInTurn(battle_unit=unit3, battle_turn=turn2, x_pos=48, z_pos=98)
    battle_unit3_in_turn3 = BattleUnitInTurn(battle_unit=unit3, battle_turn=turn3, x_pos=48, z_pos=96)
    battle_unit3_in_turn1.save()
    battle_unit3_in_turn2.save()
    battle_unit3_in_turn3.save()

    object1 = BattleObject(battle=battle)
    object1.save()
    object1_in_turn1 = BattleObjectInTurn(battle_object=object1, battle_turn=turn, x_pos=49, z_pos=98)
    object1_in_turn1.save()
    object1_in_turn2 = BattleObjectInTurn(battle_object=object1, battle_turn=turn2, x_pos=49, z_pos=98)
    object1_in_turn2.save()
    object1_in_turn3 = BattleObjectInTurn(battle_object=object1, battle_turn=turn3, x_pos=49, z_pos=98)
    object1_in_turn3.save()

    object2 = BattleObject(battle=battle)
    object2.save()
    object2_in_turn1 = BattleObjectInTurn(battle_object=object2, battle_turn=turn, x_pos=50, z_pos=98)
    object2_in_turn1.save()
    object2_in_turn2 = BattleObjectInTurn(battle_object=object2, battle_turn=turn2, x_pos=50, z_pos=98)
    object2_in_turn2.save()
    object2_in_turn3 = BattleObjectInTurn(battle_object=object2, battle_turn=turn3, x_pos=50, z_pos=98)
    object2_in_turn3.save()

    object3 = BattleObject(battle=battle)
    object3.save()
    object3_in_turn1 = BattleObjectInTurn(battle_object=object3, battle_turn=turn, x_pos=51, z_pos=98)
    object3_in_turn1.save()
    object3_in_turn2 = BattleObjectInTurn(battle_object=object3, battle_turn=turn2, x_pos=51, z_pos=98)
    object3_in_turn2.save()
    object3_in_turn3 = BattleObjectInTurn(battle_object=object3, battle_turn=turn3, x_pos=51, z_pos=98)
    object3_in_turn3.save()

    context = {
        'battle_data': json.dumps(battle.render_for_view())
    }
    return render(request, 'battle/test.html', context=context)