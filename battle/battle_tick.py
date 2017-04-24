import math

from battle.models import Battle, BattleCharacterInTurn, BattleUnitInTurn, BattleContuberniumInTurn, \
    BattleSoldierInTurn, Coordinates, Order, BattleUnit


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


def optimistic_move_desire_resolving(battle: Battle):
    while BattleContuberniumInTurn.objects.filter(desires_pos=True).exists():
        bcuit = BattleContuberniumInTurn.objects.filter(desires_pos=True)[0]
        contubernia_desiring_position = battle.get_latest_turn().get_contubernia_desiring_position(bcuit.desired_coordinates())
        desired_position_occupier = battle.get_latest_turn().get_contubernium_in_position(bcuit.desired_coordinates())

        if desired_position_occupier:
            if desired_position_occupier.desires_pos:  # test if mutually desiring position
                for desirer in contubernia_desiring_position:
                    if desirer.coordinates() == desired_position_occupier.desired_coordinates():
                        grant_position_desire(desirer)
                        grant_position_desire(desired_position_occupier)
                        continue
                # TODO: try to move blocking contubernium before giving up
                contubernia_desiring_position.update(desires_pos=False)
            else:
                contubernia_desiring_position.update(desires_pos=False)

        else:
            desire_getter = get_highest_priority_desire(contubernia_desiring_position)
            grant_position_desire(desire_getter)
            contubernia_desiring_position.update(desires_pos=False)


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
            movement_target = get_movement_target(battle_contubernium_in_turn)
            if movement_target:
                optimistic_move_desire_formulation(battle_contubernium_in_turn, movement_target)
    optimistic_move_desire_resolving(battle)

    # second pass: if could not move, do "safe" move
    for battle_unit_in_turn in BattleUnitInTurn.objects.filter(battle_turn=battle.get_latest_turn()):
        for battle_contubernium_in_turn in battle_unit_in_turn.battlecontuberniuminturn_set.filter(moved_this_turn=False):
            movement_target = get_movement_target(battle_contubernium_in_turn)
            if movement_target:
                safe_move(battle_contubernium_in_turn, movement_target)

    # finalize
    for battle_unit_in_turn in BattleUnitInTurn.objects.filter(battle_turn=battle.get_latest_turn()):
        battle_unit_in_turn.update_pos()
        check_if_order_done(battle_unit_in_turn)


def check_if_order_done(battle_unit_in_turn: BattleUnitInTurn):
    order = battle_unit_in_turn.battle_unit.get_turn_order()
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


def get_movement_target(battle_contubernium_in_turn: BattleContuberniumInTurn):
    order = battle_contubernium_in_turn.battle_unit_in_turn.battle_unit.get_turn_order()
    if order:
        if order.what == Order.STAND:
            return None
        if order.what == Order.MOVE:
            unit_target = order.target_location_coordinates()
            return Coordinates(
                x=(unit_target.x + battle_contubernium_in_turn.battle_contubernium.x_offset_to_unit),
                z=(unit_target.z + battle_contubernium_in_turn.battle_contubernium.z_offset_to_unit)
            )
        if order.what == Order.FLEE:
            pass
        if order.what == Order.CHARGE:
            pass
        if order.what == Order.ADVANCE_IN_FORMATION:
            z_direction = -1 if battle_contubernium_in_turn.battle_contubernium.battle_unit.battle_side.z else 1
            z_offset = battle_contubernium_in_turn.battle_turn.num * z_direction
            return Coordinates(
                x=battle_contubernium_in_turn.battle_contubernium.starting_x_pos,
                z=battle_contubernium_in_turn.battle_contubernium.starting_z_pos + z_offset
            )
        if order.what == Order.RANGED_ATTACK:
            pass


def optimistic_move_desire_formulation(battle_contubernium_in_turn: BattleContuberniumInTurn, target: Coordinates):
    def tile_availability_test(coords: Coordinates):
        return True

    if euclidean_distance(battle_contubernium_in_turn.coordinates(), target) > 0:
        path = find_path(battle_contubernium_in_turn, target, tile_availability_test)
        if len(path) > 1:
            battle_contubernium_in_turn.desires_pos = True
            battle_contubernium_in_turn.desired_x_pos = path[1].x
            battle_contubernium_in_turn.desired_z_pos = path[1].z
            battle_contubernium_in_turn.save()


def safe_move(battle_contubernium_in_turn: BattleContuberniumInTurn, target: Coordinates):
    def tile_availability_test(coords: Coordinates):
        return True if battle_contubernium_in_turn.battle_turn.get_contubernium_in_position(coords) is None else False

    if euclidean_distance(battle_contubernium_in_turn.coordinates(), target) > 0:
        path = find_path(battle_contubernium_in_turn, target, tile_availability_test)
        if len(path) > 1:
            battle_contubernium_in_turn.moved_this_turn = True
            battle_contubernium_in_turn.x_pos = path[1].x
            battle_contubernium_in_turn.z_pos = path[1].z
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


def find_path(battle_contubernium_in_turn: BattleContuberniumInTurn, goal, tile_availability_test) -> list:
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
                if not tile_availability_test(current):
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
            f_score[neighbor] = g_score[neighbor] + euclidean_distance(neighbor, goal)

    return []


def check_end(battle: Battle):
    pass


def battle_tick(battle: Battle):
    create_next_turn(battle)
    unit_movement(battle)
    check_end(battle)


def battle_turn(battle: Battle):
    for i in range(10):
        battle_tick(battle)
