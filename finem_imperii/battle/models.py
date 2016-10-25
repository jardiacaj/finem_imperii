from django.db import models
from django.forms.models import model_to_dict


class Battle(models.Model):
    def render_for_view(self):
        result = {
            'unit_data': [],
            'object_data': [],
            'turn_count': self.battleturn_set.count(),
            'heightmap': [0]*100
        }
        for battle_unit in self.battleunit_set.all():
            unit_data = {
                'turn_data': [model_to_dict(battle_unit_in_turn) for battle_unit_in_turn in battle_unit.battleunitinturn_set.all()]
            }
            result['unit_data'].append(unit_data)
        for battle_object in self.battleobject_set.all():
            object_data = {
                'turn_data': [model_to_dict(battle_object_in_turn) for battle_object_in_turn in battle_object.battleobjectinturn_set.all()]
            }
            result['object_data'].append(object_data)
        return result


class BattleTurn(models.Model):
    battle = models.ForeignKey(Battle)
    num = models.IntegerField()


class BattleUnit(models.Model):
    battle = models.ForeignKey(Battle)


class BattleUnitInTurn(models.Model):
    battle_unit = models.ForeignKey(BattleUnit)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()


class BattleObject(models.Model):
    battle = models.ForeignKey(Battle)


class BattleObjectInTurn(models.Model):
    battle_object = models.ForeignKey(BattleObject)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
