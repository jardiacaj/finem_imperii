import logging
from collections import namedtuple, defaultdict

import math
from heapq import heappush, heappop

from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models.aggregates import Max
from django.db.models.expressions import F
from django.forms.models import model_to_dict

Coordinates = namedtuple("Coordinates", ['x', 'z'])


class Battle(models.Model):
    def get_absolute_url(self):
        return reverse('battle:view_battle', kwargs={'battle_id': self.id})

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

    def get_latest_turn(self):
        return self.battleturn_set.order_by('-num')[0]

    def start_battle(self):
        turn = BattleTurn(battle=self, num=0)
        turn.save()

        order = Order(what="move", target_location_x=45, target_location_z=20, done=False)
        order.save()
        unit = BattleUnit(battle=self)
        unit.save()
        order_in_list = OrderListElement(order=order, battle_unit=unit, position=0)
        order_in_list.save()
        unit_in_turn = BattleUnitInTurn(battle_unit=unit, battle_turn=turn, x_pos=50, z_pos=0)
        unit_in_turn.order = order
        unit_in_turn.save()

    def do_turn(self):
        if not self.get_latest_turn():
            self.start_battle()

        prev_turn = self.get_latest_turn()
        next_turn = prev_turn.create_next()

        for unit in next_turn.battleunitinturn_set.all():
            unit.do_turn()
            unit.save()


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


class BattleUnit(models.Model):
    battle = models.ForeignKey(Battle)
    orders = models.ManyToManyField(through=OrderListElement, to=Order)


class BattleUnitInTurn(models.Model):
    class Meta:
        index_together = [
            ["battle_turn", "x_pos", "z_pos"],
        ]
    battle_unit = models.ForeignKey(BattleUnit)
    battle_turn = models.ForeignKey(BattleTurn)
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
    order = models.ForeignKey(Order, null=True)

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

    def path_heuristic(self, start, goal):
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
        cameFrom = {}
        gScore = {}
        gScore[self.coordinates()] = 0
        fScore = {}
        fScore[self.coordinates()] = self.path_heuristic(self.coordinates(), goal)

        while open_set:
            minel = None
            for el in open_set:
                if minel is None or fScore[el] < fScore[minel]:
                    minel = el
            current = minel
            open_set.remove(minel)

            if current == goal:
                # RECONSTRUCT
                #print("REACHED GOAL, backtracing")
                total_path = [current]
                while current in cameFrom.keys():
                    current = cameFrom[current]
                    total_path.append(current)
                    #print("Backtrace {}".format(current))
                total_path.reverse()
                return total_path

            closed_set.add(current)
            for neighbor in self.coordinate_neighbours(current):
                if neighbor in closed_set:
                    #print("Already closed: {}".format(neighbor))
                    continue
                tentative_gScore = gScore[current] + self.path_heuristic(current, neighbor)
                #print("Considering {} with score {}".format(neighbor, tentative_gScore))
                if neighbor not in open_set:
                    #print("Adding to open set")
                    open_set.add(neighbor)
                elif tentative_gScore >= gScore[neighbor]:
                    #print("Better value in gScore map")
                    continue

                #print("Found better path")
                cameFrom[neighbor] = current
                gScore[neighbor] = tentative_gScore
                fScore[neighbor] = gScore[neighbor] + self.path_heuristic(neighbor, goal)
        return None

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
