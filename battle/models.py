from collections import namedtuple

import math

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict

Coordinates = namedtuple("Coordinates", ['x', 'z'])


class BattleFormation(models.Model):
    class Meta:
        unique_together = (
            ('organization', 'battle')
        )

    LINE = 'line'
    COLUMN = 'column'
    SQUARE = 'square'
    WEDGE = 'wedge'
    IWEDGE = 'iwedge'
    FORMATION_CHOICES = (
        (LINE, LINE),
        (COLUMN, COLUMN),
        (SQUARE, SQUARE),
        (WEDGE, WEDGE),
        (IWEDGE, IWEDGE),
    )
    formation = models.CharField(max_length=15, choices=FORMATION_CHOICES)
    element_size = models.IntegerField(null=True, blank=True)
    spacing = models.IntegerField(null=True, blank=True)
    organization = models.ForeignKey('organization.Organization')
    battle = models.ForeignKey('Battle', null=True, blank=True)


class Battle(models.Model):
    tile = models.ForeignKey('world.Tile')
    current = models.BooleanField(default=True)
    started = models.BooleanField(default=False)
    start_turn = models.IntegerField()
    end_turn = models.IntegerField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse('battle:battlefield', kwargs={'battle_id': self.id})

    def get_latest_turn(self):
        turns = self.battleturn_set.order_by('-num')
        if not turns:
            return None
        return turns[0]

    def get_units_in_battle(self):
        return BattleUnit.objects.filter(owner__battle_organization__side__battle=self)

    def get_side_a(self):
        return self.battleside_set.all()[0]

    def get_side_b(self):
        return self.battleside_set.all()[1]


class BattleTurn(models.Model):
    class Meta:
        unique_together = (
            ("battle", "num"),
        )
    battle = models.ForeignKey(Battle)
    num = models.IntegerField()

    def create_next(self):
        new_turn = BattleTurn(battle=self.battle, num=self.num+1)
        new_turn.save()

        for unit in self.battleunitinturn_set.all():
            BattleUnitInTurn(
                battle_unit=unit.battle_unit,
                battle_turn=new_turn,
                x_pos=unit.x_pos,
                z_pos=unit.z_pos,
                order=unit.order
            ).save()

        for battle_object in self.battleobjectinturn_set.all():
            BattleObjectInTurn(
                battle_object=battle_object.battle_object,
                battle_turn=new_turn,
                x_pos=battle_object.x_pos,
                z_pos=battle_object.z_pos
            ).save()

        return new_turn


class BattleSide(models.Model):
    battle = models.ForeignKey(Battle)
    z = models.BooleanField(default=False)

    def get_largest_organization(self):
        max_found = 0
        result = None
        for organization in self.battleorganization_set.all():
            manpower = organization.get_initial_manpower()
            if manpower > max_found:
                max_found = manpower
                result = organization
        return result

    def get_formation(self):
        return self.get_largest_organization().organization.get_default_formation_settings()


class BattleOrganization(models.Model):
    side = models.ForeignKey(BattleSide)
    organization = models.ForeignKey('organization.Organization')

    def get_initial_manpower(self):
        return BattleUnit.objects.filter(owner__battle_organization=self).\
            aggregate(Sum('starting_manpower'))['starting_manpower__sum']


class BattleCharacter(models.Model):
    battle_organization = models.ForeignKey(BattleOrganization)
    character = models.ForeignKey('world.Character')


class BattleCharacterInTurn(models.Model):
    battle_character = models.ForeignKey(BattleCharacter)
    battle_turn = models.ForeignKey(BattleTurn)


class BattleUnit(models.Model):
    orders = models.ManyToManyField(through='OrderListElement', to='Order')
    battle_side = models.ForeignKey(BattleSide)
    owner = models.ForeignKey(BattleCharacter)
    world_unit = models.ForeignKey('world.WorldUnit')
    starting_x_pos = models.IntegerField(default=0)
    starting_z_pos = models.IntegerField(default=0)
    starting_manpower = models.IntegerField()
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30)

    def get_turn_order(self):
        return OrderListElement.objects.filter(battle_unit=self, order__done=False).order_by('position')[0].order

    def __str__(self):
        return self.world_unit.name


class BattleUnitInTurn(models.Model):
    class Meta:
        index_together = [
            ["battle_turn", "x_pos", "z_pos"],
        ]
    battle_unit = models.ForeignKey(BattleUnit)
    battle_character_in_turn = models.ForeignKey(BattleCharacterInTurn)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
    order = models.ForeignKey('Order', null=True)

    def coordinates(self):
        return Coordinates(self.x_pos, self.z_pos)


class BattleContubernium(models.Model):
    battle_unit = models.ForeignKey(BattleUnit)
    starting_x_pos = models.IntegerField(default=0)
    starting_z_pos = models.IntegerField(default=0)
    x_offset_to_unit = models.IntegerField(default=0, help_text="Offset to BattleUnit starting_pos")
    z_offset_to_unit = models.IntegerField(default=0)
    x_offset_to_formation = models.IntegerField(default=0)
    z_offset_to_formation = models.IntegerField(default=0)


class BattleContuberniumInTurn(models.Model):
    battle_contubernium = models.ForeignKey(BattleContubernium)
    battle_unit_in_turn = models.ForeignKey(BattleUnitInTurn)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()


class BattleSoldier(models.Model):
    world_npc = models.ForeignKey('world.NPC')
    battle_contubernium = models.ForeignKey(BattleContubernium)


class BattleSoldierInTurn(models.Model):
    battle_soldier = models.ForeignKey(BattleSoldier)
    battle_contubernium_in_turn = models.ForeignKey(BattleContuberniumInTurn)
    battle_turn = models.ForeignKey(BattleTurn)


class Order(models.Model):
    STAND = 'stand'
    MOVE = 'move'
    FLEE = 'flee'
    CHARGE = 'charge'
    ADVANCE_IN_FORMATION = 'formation'
    RANGED_ATTACK = 'ranged'
    WHAT_CHOICES = (
       (STAND, STAND),
       (MOVE, MOVE),
       (FLEE, FLEE),
       (CHARGE, CHARGE),
       (ADVANCE_IN_FORMATION, ADVANCE_IN_FORMATION),
       (RANGED_ATTACK, RANGED_ATTACK),
    )

    what = models.CharField(max_length=15, choices=WHAT_CHOICES)
    target_location_x = models.IntegerField(null=True)
    target_location_z = models.IntegerField(null=True)
    done = models.BooleanField(default=0)

    def target_location_coordinates(self):
        return Coordinates(self.target_location_x, self.target_location_z)


class OrderListElement(models.Model):
    class Meta:
        unique_together = (
            ("battle_unit", "position"),
        )
    order = models.ForeignKey(Order)
    battle_unit = models.ForeignKey('BattleUnit')
    position = models.SmallIntegerField()


class BattleObject(models.Model):
    battle = models.ForeignKey(Battle)


class BattleObjectInTurn(models.Model):
    class Meta:
        index_together = [
            ["battle_turn", "x_pos", "z_pos"],
        ]
    battle_object = models.ForeignKey(BattleObject)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
