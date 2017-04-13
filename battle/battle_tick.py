import math

from battle.models import Battle, BattleCharacterInTurn, BattleUnitInTurn, BattleContuberniumInTurn, \
    BattleSoldierInTurn, Coordinates, Order


def create_next_turn(battle: Battle):
    new_turn = battle.get_latest_turn()
    new_turn.id = None
    new_turn.num += 1
    new_turn.save()
    prev_turn = battle.battleturn_set.get(num=new_turn.num - 1)

    for side in battle.battleside_set.all():
        for organization in side.battleorganization_set.all():
            for character in organization.battlecharacter_set.all():
                bcit = BattleCharacterInTurn.objects.get(battle_character=character, battle_turn=prev_turn)
                bcit.id = None
                bcit.battle_turn = new_turn
                bcit.save()

                for unit in character.battleunit_set.all():
                    buit = BattleUnitInTurn.objects.get(battle_unit=unit, battle_turn=prev_turn)
                    buit.id = None
                    buit.battle_turn = new_turn
                    buit.battle_character_in_turn = bcit
                    buit.order = buit.battle_unit.get_turn_order()
                    buit.save()

                    for contubernium in unit.battlecontubernium_set.all():
                        bcontubit = BattleContuberniumInTurn.objects.get(
                            battle_contubernium=contubernium, battle_turn=prev_turn
                        )
                        bcontubit.id = None
                        bcontubit.battle_turn = new_turn
                        bcontubit.battle_unit_in_turn = buit
                        bcontubit.save()

                        for soldier in contubernium.battlesoldier_set.all():
                            bsit = BattleSoldierInTurn.objects.get(
                                battle_turn=prev_turn,
                                battle_soldier=soldier
                            )
                            bsit.id = None
                            bsit.battle_turn = new_turn
                            bsit.battle_contubernium_in_turn = bcontubit
                            bsit.save()

                        do_turn(bcontubit)

                    buit.update_pos()


def do_turn(battle_contubernium_in_turn: BattleContuberniumInTurn):
    order = battle_contubernium_in_turn.battle_unit_in_turn.battle_unit.get_turn_order()
    if order:
        if order.what == Order.STAND:
            pass
        if order.what == Order.MOVE:
            unit_target = order.target_location_coordinates()
            contub_target = Coordinates(
                x=(unit_target.x + battle_contubernium_in_turn.battle_contubernium.x_offset_to_unit),
                z=(unit_target.z + battle_contubernium_in_turn.battle_contubernium.z_offset_to_unit)
            )
            if euclidean_distance(battle_contubernium_in_turn.coordinates(), contub_target) > 0:
                path = find_path(
                    battle_contubernium_in_turn,
                    contub_target
                )
                if len(path) > 1:
                    battle_contubernium_in_turn.x_pos = path[1].x
                    battle_contubernium_in_turn.z_pos = path[1].z
        if order.what == Order.FLEE:
            pass
        if order.what == Order.CHARGE:
            pass
        if order.what == Order.ADVANCE_IN_FORMATION:
            pass
        if order.what == Order.RANGED_ATTACK:
            pass
    battle_contubernium_in_turn.save()


def euclidean_distance(start: Coordinates, goal: Coordinates):
    return math.sqrt((start.x - goal.x)**2 + (start.z - goal.z)**2)


def coordinate_neighbours(coord: Coordinates):
    result = []
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if not dx == dz == 0:
                result.append(Coordinates(coord.x + dx, coord.z + dz))
    return result


def find_path(battle_contubernium_in_turn: BattleContuberniumInTurn, goal):
    if euclidean_distance(battle_contubernium_in_turn.coordinates(), goal) == 0:
        return True

    closed_set = set()
    open_set = set()
    open_set.add((battle_contubernium_in_turn.coordinates()))
    came_from = {}
    g_score = {}
    g_score[battle_contubernium_in_turn.coordinates()] = 0
    f_score = {}
    f_score[battle_contubernium_in_turn.coordinates()] = euclidean_distance(battle_contubernium_in_turn.coordinates(), goal)

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
        for neighbor in coordinate_neighbours(current):
            if neighbor in closed_set:
                # print("Already closed: {}".format(neighbor))
                continue
            tentative_g_score = g_score[current] + euclidean_distance(current, neighbor)
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
            f_score[neighbor] = g_score[neighbor] + euclidean_distance(neighbor, goal)
    return None


def check_end(battle: Battle):
    pass


def battle_tick(battle: Battle):
    create_next_turn(battle)
    check_end(battle)
