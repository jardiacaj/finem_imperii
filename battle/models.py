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

    def get_absolute_url(self):
        return reverse('battle:view_battle', kwargs={'battle_id': self.id})

    def get_latest_turn(self):
        turns = self.battleturn_set.order_by('-num')
        if not turns:
            return None
        return turns[0]

    def get_units_in_battle(self):
        return BattleUnit.objects.filter(owner__battle_organization__side__battle=self)

    def initialize_from_conflict(self, conflict, tile):
        z = False
        for organization in conflict:
            battle_side = BattleSide.objects.create(battle=self, z=z)
            BattleOrganization.objects.create(side=battle_side, organization=organization)
            z = True
        for unit in tile.get_units():
            violence_monopoly = unit.owner_character.get_violence_monopoly()
            if violence_monopoly in conflict:
                battle_organization = BattleOrganization.objects.get(side__battle=self, organization=violence_monopoly)
                battle_character = BattleCharacter.objects.get_or_create(
                    battle_organization=battle_organization,
                    character=unit.owner_character,
                )[0]
                battle_unit = BattleUnit.objects.create(
                    owner=battle_character,
                    world_unit=unit,
                    starting_manpower=unit.get_fighting_soldiers().count(),
                    battle_side=battle_organization.side
                )

    def start_battle(self):
        for unit in self.get_units_in_battle().all():
            unit.create_contubernia()
        self.initialize_positioning()

    def initialize_positioning(self):
        for side in self.battleside_set.all():
            side.initialize_positioning()

    def render_for_view(self):
        result = {
            'unit_data': [],
            'object_data': [],
            'turn_count': self.battleturn_set.count(),
            'heightmap': [0]*100
        }
        for char in self.battlecharacter_set.all():
            for battle_unit in char.battleunit_set.all():
                unit_data = {
                    'turn_data': [
                        model_to_dict(battle_unit_in_turn)
                        for battle_unit_in_turn in battle_unit.battleunitinturn_set.all()
                    ]
                }
                result['unit_data'].append(unit_data)
        for battle_object in self.battleobject_set.all():
            object_data = {
                'turn_data': [
                    model_to_dict(battle_object_in_turn)
                    for battle_object_in_turn in battle_object.battleobjectinturn_set.all()
                ]
            }
            result['object_data'].append(object_data)
        return result


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
        return self.get_largest_organization().organization.get_default_formation()

    def initialize_positioning(self):
        formation = self.get_formation()
        if formation == BattleFormation.LINE:
            self.initialize_line_formation()

    def initialize_line_formation(self):
        pass


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

    def create_contubernia(self):
        soldiers = self.world_unit.get_fighting_soldiers()
        num_contubernia = math.ceil(soldiers.count()/8)
        rest = soldiers.count() % 8
        pointer = 0
        for i in range(num_contubernia):
            start = pointer
            end = pointer + (8 if i < rest else 7)
            contubernium_soldiers = soldiers[start:end]
            contubernium = BattleContubernium.objects.create(battle_unit=self)
            for soldier in contubernium_soldiers:
                BattleSoldier.objects.create(battle_contubernium=contubernium, world_npc=soldier)
            pointer = end

    def __str__(self):
        return self.world_unit.name


class BattleUnitInTurn(models.Model):
    class Meta:
        index_together = [
            ["battle_turn", "x_pos", "z_pos"],
        ]
    battle_unit = models.ForeignKey(BattleUnit)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
    order = models.ForeignKey('Order', null=True)

    def coordinates(self):
        return Coordinates(self.x_pos, self.z_pos)

    def do_turn(self):
        if self.order:
            if self.order.what == 'move':
                path = self.find_path(self.order.target_location_coordinates())
                print(path)
                if len(path) > 1:
                    self.x_pos = path[1].x
                    self.z_pos = path[1].z
            if self.order.what == 'attack':
                pass
            if self.order.what == 'stand':
                pass

    def euclidean_distance(self, start, goal):
        return math.sqrt((start.x - goal.x)**2 + (start.z - goal.z)**2)

    def coordinate_neighbours(self, coord):
        result = []
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if not dx == dz == 0:
                    result.append(Coordinates(coord.x + dx, coord.z + dz))
        return result

    def find_path(self, goal):
        closed_set = set()
        open_set = set()
        open_set.add((self.coordinates()))
        came_from = {}
        g_score = {}
        g_score[self.coordinates()] = 0
        f_score = {}
        f_score[self.coordinates()] = self.euclidean_distance(self.coordinates(), goal)

        while open_set:
            minel = None
            for el in open_set:
                if minel is None or f_score[el] < f_score[minel]:
                    minel = el
            current = minel
            open_set.remove(minel)

            if current == goal:
                # RECONSTRUCT
                # print("REACHED GOAL, backtracing")
                total_path = [current]
                while current in came_from.keys():
                    current = came_from[current]
                    total_path.append(current)
                    # print("Backtrace {}".format(current))
                total_path.reverse()
                return total_path

            closed_set.add(current)
            for neighbor in self.coordinate_neighbours(current):
                if neighbor in closed_set:
                    # print("Already closed: {}".format(neighbor))
                    continue
                tentative_g_score = g_score[current] + self.euclidean_distance(current, neighbor)
                # print("Considering {} with score {}".format(neighbor, tentative_g_score))
                if neighbor not in open_set:
                    # print("Adding to open set")
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score[neighbor]:
                    # print("Better value in g_score map")
                    continue

                # print("Found better path")
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self.euclidean_distance(neighbor, goal)
        return None


class BattleContubernium(models.Model):
    battle_unit = models.ForeignKey(BattleUnit)


class BattleContuberniumInTurn(models.Model):
    battle_contubernium = models.ForeignKey(BattleContubernium)


class BattleSoldier(models.Model):
    world_npc = models.ForeignKey('world.NPC')
    battle_contubernium = models.ForeignKey(BattleContubernium)


class BattleSoldierInTurn(models.Model):
    battle_soldier = models.ForeignKey(BattleSoldier)


class Order(models.Model):
    what = models.CharField(max_length=15)
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
