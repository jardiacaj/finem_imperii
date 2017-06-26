import math
import random

import django
from django.db import transaction

from battle.models import Battle, BattleCharacterInTurn, BattleUnitInTurn, BattleContuberniumInTurn, \
    BattleSoldierInTurn, Coordinates, Order, BattleUnit
from finem_imperii.app_settings import BATTlE_TICKS_PER_TURN
from world.models import WorldUnit


def create_next_turn(battle: Battle):
    new_turn = battle.get_latest_turn()
    new_turn.id = None
    new_turn.num += 1
    new_turn.save()
    prev_turn = battle.battleturn_set.get(num=new_turn.num - 1)

    for side in battle.battleside_set.all():
        for organization in side.battleorganization_set.all():
            for character in organization.battlecharacter_set.all():
                bcit = BattleCharacterInTurn.objects.get(
                    battle_character=character,
                    battle_turn=prev_turn
                )
                bcit.id = None
                bcit.battle_turn = new_turn
                bcit.save()

            for unit in organization.battleunit_set.all():
                try:
                    buit = BattleUnitInTurn.objects.get(
                        battle_unit=unit,
                        battle_turn=prev_turn
                    )
                    if not buit.battlecontuberniuminturn_set.filter(
                        x_pos__gte=-50, x_pos__lte=50,
                        z_pos__gte=-50, z_pos__lte=50,
                    ).exists():
                        buit.battle_unit.in_battle = False
                        buit.battle_unit.save()
                        buit.battle_unit.world_unit.status = \
                            WorldUnit.REGROUPING
                        buit.battle_unit.world_unit.save()
                        continue
                    if not BattleSoldierInTurn.objects.filter(
                        battle_contubernium_in_turn__battle_unit_in_turn=buit,
                        wound_status__lt=BattleSoldierInTurn.DEAD
                    ).exists():
                        buit.battle_unit.in_battle = False
                        buit.battle_unit.save()
                        buit.battle_unit.world_unit.status = \
                            WorldUnit.REGROUPING
                        buit.battle_unit.world_unit.save()
                        continue
                    buit.id = None
                    buit.battle_turn = new_turn
                    buit.battle_character_in_turn = BattleCharacterInTurn.objects.get(
                        battle_turn=new_turn,
                        battle_character=buit.battle_character_in_turn.battle_character
                    ) if buit.battle_character_in_turn is not None else None
                    buit.order = buit.battle_unit.get_order()
                    buit.save()
                except BattleUnitInTurn.DoesNotExist:
                    continue

                for contubernium in unit.battlecontubernium_set.all():

                    try:
                        bcontubit = BattleContuberniumInTurn.objects.get(
                            battle_contubernium=contubernium,
                            battle_turn=prev_turn
                        )
                        if not bcontubit.battlesoldierinturn_set.filter(
                            wound_status__lt=BattleSoldierInTurn.DEAD
                        ).exists():
                            continue
                        if (
                                    not -50 <= bcontubit.x_pos <= 50 or
                                    not -50 <= bcontubit.z_pos <= 50
                        ):
                            continue
                        bcontubit.id = None
                        bcontubit.moved_this_turn = False
                        bcontubit.desires_pos = False
                        bcontubit.battle_turn = new_turn
                        bcontubit.battle_unit_in_turn = buit
                        bcontubit.save()
                    except BattleContuberniumInTurn.DoesNotExist:
                        pass

                    for soldier in contubernium.battlesoldier_set.all():
                        try:
                            bsit = BattleSoldierInTurn.objects.get(
                                battle_turn=prev_turn,
                                battle_soldier=soldier
                            )
                            if bsit.wound_status == BattleSoldierInTurn.DEAD:
                                continue
                            bsit.id = None
                            bsit.battle_turn = new_turn
                            bsit.battle_contubernium_in_turn = bcontubit
                            bsit.save()
                        except BattleSoldierInTurn.DoesNotExist:
                            pass


def optimistic_move_desire_resolving(battle: Battle):
    while BattleContuberniumInTurn.objects.filter(desires_pos=True, battle_turn=battle.get_latest_turn()).exists():
        bcuit = BattleContuberniumInTurn.objects.filter(desires_pos=True, battle_turn=battle.get_latest_turn())[0]
        contubernia_desiring_position = battle.get_latest_turn().get_contubernia_desiring_position(bcuit.desired_coordinates())
        desired_position_occupier = battle.get_latest_turn().get_contubernium_in_position(bcuit.desired_coordinates())

        if desired_position_occupier:
            # test if mutually desiring positions
            if desired_position_occupier.desires_pos:
                for desirer in contubernia_desiring_position:
                    if desirer.coordinates() == desired_position_occupier.desired_coordinates():
                        grant_position_swap(desirer, desired_position_occupier)
                        continue
                # TODO: try to move blocking contubernium before giving up
                contubernia_desiring_position.update(desires_pos=False)
            else:
                contubernia_desiring_position.update(desires_pos=False)

        else:
            desire_getter = get_highest_priority_desire(contubernia_desiring_position)
            grant_position_desire(desire_getter)
            contubernia_desiring_position.update(desires_pos=False)


def grant_position_swap(contubernium1: BattleContuberniumInTurn, contubernium2: BattleContuberniumInTurn):
    contubernium1.x_pos = 31337
    contubernium1.save()
    grant_position_desire(contubernium2)
    grant_position_desire(contubernium1)


def grant_position_desire(desire_getter: BattleContuberniumInTurn):
    desire_getter.desires_pos = False
    desire_getter.moved_this_turn = True
    desire_getter.x_pos = desire_getter.desired_x_pos
    desire_getter.z_pos = desire_getter.desired_z_pos
    desire_getter.save()


def get_highest_priority_desire(contubernium_list: list) -> BattleContuberniumInTurn:
    highest_prio = -1
    result = None
    for contubernium in contubernium_list:
        order = contubernium.battle_unit_in_turn.order
        what = order.what if order else Order.STAND
        prio = Order.ORDER_PRIORITY[what]
        if prio > highest_prio:
            result = contubernium
            highest_prio = prio
    return result


def unit_movement(battle: Battle):
    # first pass: desire positions / optimistic move
    for battle_unit_in_turn in BattleUnitInTurn.objects.filter(battle_turn=battle.get_latest_turn()):
        for battle_contubernium_in_turn in battle_unit_in_turn.battlecontuberniuminturn_set.all():
            target_distance_function = get_target_distance_function(battle_contubernium_in_turn)
            if target_distance_function:
                optimistic_move_desire_formulation(battle_contubernium_in_turn, target_distance_function)
    optimistic_move_desire_resolving(battle)

    # second pass: if could not move, do "safe" move
    for battle_unit_in_turn in BattleUnitInTurn.objects.filter(battle_turn=battle.get_latest_turn()):
        for battle_contubernium_in_turn in battle_unit_in_turn.battlecontuberniuminturn_set.filter(moved_this_turn=False):
            target_distance_function = get_target_distance_function(battle_contubernium_in_turn)
            if target_distance_function:
                safe_move(battle_contubernium_in_turn, target_distance_function)

    # finalize
    for battle_unit_in_turn in BattleUnitInTurn.objects.filter(battle_turn=battle.get_latest_turn()):
        battle_unit_in_turn.update_pos()
        check_if_order_done(battle_unit_in_turn)


def check_if_order_done(battle_unit_in_turn: BattleUnitInTurn):
    order = battle_unit_in_turn.battle_unit.get_order()
    if order:
        if order.what == Order.STAND:
            pass
        if order.what == Order.MOVE:
            if euclidean_distance(battle_unit_in_turn.coordinates(), order.target_location_coordinates()) == 0:
                order.done = True
                order.save()
        if order.what == Order.FLEE:
            pass
        if order.what == Order.CHARGE:
            pass
        if order.what == Order.ADVANCE_IN_FORMATION:
            pass
        if order.what == Order.RANGED_ATTACK:
            pass


def closest_in_set(coords, contubernium_set):
    closest = None
    distance = None
    for contubernium in contubernium_set:
        tentative_distance = euclidean_distance(coords, contubernium.coordinates())
        if closest is None or tentative_distance < distance:
            closest = contubernium
            distance = tentative_distance
    return closest, distance


def get_target_distance_function(battle_contubernium_in_turn: BattleContuberniumInTurn):
    order = battle_contubernium_in_turn.battle_unit_in_turn.battle_unit.get_order()
    enemy_contubernia = BattleContuberniumInTurn.objects.filter(
        battle_turn=battle_contubernium_in_turn.battle_turn
    ).exclude(
        battle_contubernium__battle_unit__battle_side=
        battle_contubernium_in_turn.battle_contubernium.battle_unit.battle_side
    )

    if order:

        if order.what == Order.STAND:
            return None

        if order.what == Order.MOVE:
            unit_target = order.target_location_coordinates()
            target = Coordinates(
                x=(unit_target.x + battle_contubernium_in_turn.battle_contubernium.x_offset_to_unit),
                z=(unit_target.z + battle_contubernium_in_turn.battle_contubernium.z_offset_to_unit)
            )

            def result(coords: Coordinates):
                return euclidean_distance(coords, target)
            return result

        if order.what == Order.FLEE:
            original_enemy_distance = closest_in_set(battle_contubernium_in_turn.coordinates(), enemy_contubernia)[1]

            def result(coords: Coordinates):
                closest, distance = closest_in_set(coords, enemy_contubernia)
                return (original_enemy_distance + 10) - distance if distance is not None else 0
            return result

        if order.what == Order.CHARGE:
            def result(coords: Coordinates):
                closest, distance = closest_in_set(coords, enemy_contubernia)
                return distance if distance is not None and distance >= 2 else 0
            return result

        if order.what == Order.ADVANCE_IN_FORMATION:
            z_direction = -1 if battle_contubernium_in_turn.battle_contubernium.battle_unit.battle_side.z else 1
            z_offset = battle_contubernium_in_turn.battle_turn.num * z_direction
            target = Coordinates(
                x=battle_contubernium_in_turn.battle_contubernium.starting_x_pos,
                z=battle_contubernium_in_turn.battle_contubernium.starting_z_pos + z_offset
            )

            def result(coords: Coordinates):
                return euclidean_distance(coords, target)
            return result

        if order.what == Order.RANGED_ATTACK:
            pass


def optimistic_move_desire_formulation(battle_contubernium_in_turn: BattleContuberniumInTurn, target_distance_function):
    def tile_availability_test(coords: Coordinates):
        return True

    if target_distance_function(battle_contubernium_in_turn.coordinates()) > 0:
        path = find_path(battle_contubernium_in_turn, target_distance_function, tile_availability_test)
        if len(path) > 1:
            battle_contubernium_in_turn.desires_pos = True
            battle_contubernium_in_turn.desired_x_pos = path[1].x
            battle_contubernium_in_turn.desired_z_pos = path[1].z
            battle_contubernium_in_turn.save()


def safe_move(battle_contubernium_in_turn: BattleContuberniumInTurn, target_distance_function):
    turn = battle_contubernium_in_turn.battle_turn

    def tile_availability_test(coords: Coordinates):
        return True if turn.get_contubernium_in_position(coords) is None else False

    if target_distance_function(battle_contubernium_in_turn.coordinates()) > 0:
        path = find_path(battle_contubernium_in_turn, target_distance_function, tile_availability_test)
        if len(path) > 1:
            battle_contubernium_in_turn.moved_this_turn = True
            battle_contubernium_in_turn.x_pos = path[1].x
            battle_contubernium_in_turn.z_pos = path[1].z
            #TODO WARNING: HORRIBLE HACK STARTS HERE
            #(to avoid unique constraint errors when contubs overlap for some reason)
            with transaction.atomic():
                try:
                    battle_contubernium_in_turn.save()
                except django.db.utils.IntegrityError as e:
                    pass


def euclidean_distance(start: Coordinates, goal: Coordinates):
    return math.sqrt((start.x - goal.x)**2 + (start.z - goal.z)**2)


def coordinate_neighbours(coord: Coordinates):
    result = []
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if not dx == dz == 0:
                result.append(Coordinates(coord.x + dx, coord.z + dz))
    return result


def find_path(battle_contubernium_in_turn: BattleContuberniumInTurn, target_distance_function, tile_availability_test) -> list:
    starting_coordinates = battle_contubernium_in_turn.coordinates()
    if target_distance_function(starting_coordinates) <= 0:
        return True

    closed_set = set()
    open_set = set()
    open_set.add(starting_coordinates)
    came_from = {}
    g_score = {}
    g_score[starting_coordinates] = 0
    f_score = {}
    f_score[starting_coordinates] = target_distance_function(starting_coordinates)

    while open_set:
        minel = None
        for el in open_set:
            if minel is None or f_score[el] < f_score[minel]:
                minel = el
        current = minel
        open_set.remove(minel)

        if target_distance_function(current) <= 0:
            # RECONSTRUCT
            # print("REACHED GOAL, backtracing")
            total_path = [current]
            while current in came_from.keys():
                current = came_from[current]
                if current != starting_coordinates and not tile_availability_test(current):
                    return []
                total_path.append(current)
                # print("Backtrace {}".format(current))
            total_path.reverse()
            return total_path

        closed_set.add(current)
        for neighbor in coordinate_neighbours(current):
            if neighbor in closed_set:
                # print("Already closed: {}".format(neighbor))
                continue
            tentative_g_score = g_score[current] + euclidean_distance(current, neighbor)
            if not tile_availability_test(neighbor):
                tentative_g_score += 20
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
            f_score[neighbor] = g_score[neighbor] + target_distance_function(neighbor)

    return []


def unit_attack(battle: Battle):
    contubernia = list(BattleContuberniumInTurn.objects.filter(
        battle_turn=battle.get_latest_turn()
    ))
    random.shuffle(contubernia)
    for contubernium in contubernia:
        enemy_contubernia = BattleContuberniumInTurn.objects.filter(
            battle_turn=contubernium.battle_turn
        ).exclude(
            battle_contubernium__battle_unit__battle_side=
            contubernium.battle_contubernium.battle_unit.battle_side
        )
        target_contubernium, distance = \
            closest_in_set(contubernium.coordinates(), enemy_contubernia)
        if target_contubernium is not None and distance < 2:
            for soldier in contubernium.battlesoldierinturn_set.all():
                target_soldier = random.choice(
                    target_contubernium.battlesoldierinturn_set.all()[:]
                )
                while (random.random() <
                       0.5 * soldier.attack_chance_multiplier()):
                    if target_soldier.wound_status < BattleSoldierInTurn.DEAD:
                        target_soldier.take_hit()
                target_soldier.save()


def check_end(battle: Battle):
    for side in battle.battleside_set.all():
        if not BattleSoldierInTurn.objects.filter(
            battle_turn=battle.get_latest_turn(),
            battle_contubernium_in_turn__battle_contubernium__battle_unit__battle_side=side,
            wound_status__lt=BattleSoldierInTurn.DEAD
        ).exists():
            return True
    side_0_contubs = BattleContuberniumInTurn.objects.filter(
        battle_turn=battle.get_latest_turn(),
        battle_contubernium__battle_unit__battle_side__z=False
    )
    side_1_contubs = BattleContuberniumInTurn.objects.filter(
        battle_turn=battle.get_latest_turn(),
        battle_contubernium__battle_unit__battle_side__z=False
    )
    for contub in side_0_contubs:
        closest, distance = closest_in_set(
            contub.coordinates(), side_1_contubs
        )
        if distance is not None and distance < 40:
            return False
    return True


def battle_tick(battle: Battle):
    create_next_turn(battle)
    unit_movement(battle)
    unit_attack(battle)
    if check_end(battle):
        battle.current = False
        battle.save()


def battle_turn(battle: Battle):
    for i in range(BATTlE_TICKS_PER_TURN):
        battle.refresh_from_db()
        if battle.current:
            battle_tick(battle)

    battle.tile.world.broadcast(
        (
            "The battle in {} continues".format(battle.tile)
            if battle.current else
            "The battle in {} has ended".format(battle.tile)
        ),
        'battle',
        battle.get_absolute_url()
    )
