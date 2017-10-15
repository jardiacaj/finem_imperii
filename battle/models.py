from collections import namedtuple, defaultdict

import math

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.aggregates import Sum, Avg

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
        return BattleUnit.objects.filter(battle_side__battle=self)

    def get_side_a(self):
        return self.battleside_set.all()[0]

    def get_side_b(self):
        return self.battleside_set.all()[1]

    def __str__(self):
        return "{current} battle in {tile}".format(
            current='Current' if self.current else 'Past',
            tile=self.tile
        )


class BattleTurn(models.Model):
    class Meta:
        unique_together = (
            ("battle", "num"),
        )
    battle = models.ForeignKey(Battle)
    num = models.IntegerField()

    def test_contubernia_superposition(self):
        occupied = set()
        contubernia = BattleContuberniumInTurn.objects.filter(battle_turn=self)
        for contubernium in contubernia:
            if contubernium.coordinates() in occupied:
                return True
            occupied.add(contubernium.coordinates())

    def get_contubernia_by_desired_position(self) -> dict:
        result = defaultdict(list)
        for contubernium in BattleContuberniumInTurn.objects.filter(battle_turn=self, desires_pos=True):
            result[contubernium.desired_coordinates()].append(contubernium)
        return result

    def get_contubernia_desiring_position(self, coords: Coordinates):
        return BattleContuberniumInTurn.objects.filter(
            battle_turn=self,
            desires_pos=True,
            desired_x_pos=coords.x,
            desired_z_pos=coords.z
        )

    def get_contubernium_in_position(self, coords: Coordinates):
        try:
            return BattleContuberniumInTurn.objects.get(
                battle_turn=self,
                x_pos=coords.x,
                z_pos=coords.z
            )
        except BattleContuberniumInTurn.DoesNotExist:
            return None


class BattleSide(models.Model):
    battle = models.ForeignKey(Battle)
    z = models.BooleanField(default=False)

    def get_largest_organization(self):
        max_found = -1
        result = None
        for organization in self.battleorganization_set.all():
            manpower = organization.get_initial_manpower()
            if manpower > max_found:
                max_found = manpower
                result = organization
        return result

    def get_formation(self):
        return self.get_largest_organization().organization.get_default_formation_settings()

    def get_manpower(self, turn: BattleTurn = None):
        if turn is None:
            turn = self.battle.get_latest_turn()

        return BattleSoldierInTurn.objects.filter(
            battle_turn=turn,
            wound_status__lt=BattleSoldierInTurn.HEAVY_WOUND,
            battle_contubernium_in_turn__battle_contubernium__battle_unit__battle_side=self
        ).count()

    def get_proportional_strength(self, turn: BattleTurn = None):
        if turn is None:
            turn = self.battle.get_latest_turn()
        opponent_side = self.battle.battleside_set.get(z=not self.z)
        own_manpower = self.get_manpower(turn)
        opponent_manpower = opponent_side.get_manpower(turn)
        if opponent_manpower == 0:
            return None
        return own_manpower / opponent_manpower


class BattleOrganization(models.Model):
    side = models.ForeignKey(BattleSide)
    organization = models.ForeignKey('organization.Organization')

    def get_initial_manpower(self):
        return BattleUnit.objects.filter(battle_organization=self).\
            aggregate(Sum('starting_manpower'))['starting_manpower__sum']


class BattleCharacter(models.Model):
    battle_organization = models.ForeignKey(BattleOrganization)
    character = models.ForeignKey('world.Character')
    present_in_battle = models.BooleanField()


class BattleCharacterInTurn(models.Model):
    battle_character = models.ForeignKey(BattleCharacter)
    battle_turn = models.ForeignKey(BattleTurn)


class BattleUnit(models.Model):
    battle_side = models.ForeignKey(BattleSide)
    owner = models.ForeignKey(BattleCharacter, blank=True, null=True)
    battle_organization = models.ForeignKey(BattleOrganization)
    world_unit = models.ForeignKey('world.WorldUnit')
    starting_x_pos = models.IntegerField(default=0)
    starting_z_pos = models.IntegerField(default=0)
    starting_manpower = models.IntegerField()
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30)
    in_battle = models.BooleanField(default=True)

    def get_order(self):
        if self.world_unit.owner_character:
            return self.world_unit.default_battle_orders
        else:
            strength_proportion = self.battle_side.get_proportional_strength()
            if strength_proportion is not None and strength_proportion < 0.6:
                what = Order.FLEE
            elif self.battle_side.battle.get_latest_turn().num < 10:
                what = Order.ADVANCE_IN_FORMATION
            else:
                what = Order.CHARGE

            if self.world_unit.default_battle_orders:
                self.world_unit.default_battle_orders.what = what
                self.world_unit.default_battle_orders.save()
            else:
                self.world_unit.default_battle_orders = Order.objects.create(
                    what=what)
                self.world_unit.save()
            return self.world_unit.default_battle_orders

    def __str__(self):
        return self.world_unit.name


class BattleUnitInTurn(models.Model):
    battle_unit = models.ForeignKey(BattleUnit)
    battle_character_in_turn = models.ForeignKey(BattleCharacterInTurn,
                                                 blank=True, null=True)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
    order = models.ForeignKey('Order', null=True)

    def coordinates(self):
        return Coordinates(self.x_pos, self.z_pos)

    def update_pos(self):
        aggregation = self.battlecontuberniuminturn_set.all().aggregate(
            avg_x=Avg('x_pos'),
            avg_z=Avg('z_pos')
        )
        self.x_pos = math.floor(aggregation['avg_x'])
        self.z_pos = math.floor(aggregation['avg_z'])
        self.save()


class BattleContubernium(models.Model):
    battle_unit = models.ForeignKey(BattleUnit)
    starting_x_pos = models.IntegerField(default=0)
    starting_z_pos = models.IntegerField(default=0)
    x_offset_to_unit = models.IntegerField(
        default=0, help_text="Offset to BattleUnit starting_pos"
    )
    z_offset_to_unit = models.IntegerField(default=0)
    x_offset_to_formation = models.IntegerField(default=0)
    z_offset_to_formation = models.IntegerField(default=0)


class BattleContuberniumInTurn(models.Model):
    class Meta:
        unique_together = [
            ["battle_turn", "x_pos", "z_pos"],
        ]
    battle_contubernium = models.ForeignKey(BattleContubernium)
    battle_unit_in_turn = models.ForeignKey(BattleUnitInTurn)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
    moved_this_turn = models.BooleanField(default=False)
    desires_pos = models.BooleanField(default=False)
    desired_x_pos = models.IntegerField(blank=True, null=True)
    desired_z_pos = models.IntegerField(blank=True, null=True)

    def coordinates(self):
        return Coordinates(self.x_pos, self.z_pos)

    def desired_coordinates(self):
        return Coordinates(self.desired_x_pos, self.desired_z_pos) if self.desires_pos else None


class BattleSoldier(models.Model):
    world_npc = models.ForeignKey('world.NPC')
    battle_contubernium = models.ForeignKey(BattleContubernium)


class BattleSoldierInTurn(models.Model):
    UNINJURED = 0
    LIGHT_WOUND = 1
    MEDIUM_WOUND = 2
    HEAVY_WOUND = 3
    DEAD = 4
    WOUND_STATUS_CHOICES = (
       (UNINJURED, UNINJURED),
       (LIGHT_WOUND, LIGHT_WOUND),
       (MEDIUM_WOUND, MEDIUM_WOUND),
       (HEAVY_WOUND, HEAVY_WOUND),
       (DEAD, DEAD),
    )

    ATTACK_CHANGE_MULTIPLIERS = {
        UNINJURED: 1,
        LIGHT_WOUND: 0.75,
        MEDIUM_WOUND: 0.4,
        HEAVY_WOUND: 0.1,
        DEAD: 0,
    }

    battle_soldier = models.ForeignKey(BattleSoldier)
    battle_contubernium_in_turn = models.ForeignKey(BattleContuberniumInTurn)
    battle_turn = models.ForeignKey(BattleTurn)
    wound_status = models.SmallIntegerField(
        choices=WOUND_STATUS_CHOICES, default=UNINJURED
    )

    def attack_chance_multiplier(self):
        return self.ATTACK_CHANGE_MULTIPLIERS[self.wound_status]

    def take_hit(self):
        self.wound_status += 1
        self.save()
        self.battle_soldier.world_npc.take_hit()


class Order(models.Model):
    STAND = 'stand'
    MOVE = 'move'
    FLEE = 'flee'
    CHARGE = 'charge'
    ADVANCE_IN_FORMATION = 'formation'
    RANGED_AND_CHARGE = 'ranged and charge'
    RANGED_AND_FLEE = 'ranged and flee'
    RANGED_AND_STAND = 'ranged and stand'
    WHAT_CHOICES = (
       (STAND, STAND),
       (MOVE, MOVE),
       (FLEE, FLEE),
       (CHARGE, CHARGE),
       (ADVANCE_IN_FORMATION, ADVANCE_IN_FORMATION),
       (RANGED_AND_CHARGE, "ranged attack, then charge"),
       (RANGED_AND_FLEE, "ranged attack, then flee"),
       (RANGED_AND_STAND, "ranged attack, then stand"),
    )
    ORDER_PRIORITY = {
        STAND: 4,
        MOVE: 0,
        FLEE: 3,
        CHARGE: 0,
        ADVANCE_IN_FORMATION: 2,
        RANGED_AND_CHARGE: 1,
        RANGED_AND_FLEE: 1,
        RANGED_AND_STAND: 1,
    }

    what = models.CharField(max_length=15, choices=WHAT_CHOICES)
    target_location_x = models.IntegerField(null=True)
    target_location_z = models.IntegerField(null=True)
    done = models.BooleanField(default=0)

    def target_location_coordinates(self):
        return Coordinates(self.target_location_x, self.target_location_z)


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
