import organization.models
import unit.models
from battle.battle_init import start_battle, initialize_from_conflict, \
    add_unit_to_battle_in_progress
from battle.battle_tick import battle_turn
from battle.models import Battle, BattleOrganization
from world.models.geography import World


def worldwide_trigger_battles(world: World):
    for tile in world.tile_set.all():
        if not Battle.objects.filter(
                tile=tile,
                end_turn=world.current_turn).exists():
            trigger_battles_in_tile(tile)


def trigger_battles_in_tile(tile):
    conflicts = opponents_in_organization_list(
        organizations_with_battle_ready_units(tile),
        tile
    )
    for conflict in conflicts:
        add_allies(conflict, tile)
    conflict = get_largest_conflict_in_list(conflicts, tile)
    if conflict:
        return create_battle_from_conflict(conflict, tile)


def worldwide_battle_joins(world: World):
    for battle in Battle.objects.filter(
            tile__world=world, current=True
    ):
        battle_joins(battle)


def worldwide_battle_starts(world: World):
    for battle in Battle.objects.filter(
            tile__world=world, current=True, started=False
    ):
        start_battle(battle)


def worldwide_battle_turns(world: World):
    for battle in Battle.objects.filter(
            tile__world=world, current=True
    ):
        battle_turn(battle)


def organizations_with_battle_ready_units(tile):
    result = []
    for unit in battle_ready_units_in_tile(tile):
        violence_monopoly = unit.get_violence_monopoly()
        if violence_monopoly and violence_monopoly not in result:
            result.append(violence_monopoly)
    return result


def battle_ready_units_in_tile(tile):
    return tile.get_units().\
        exclude(status=unit.models.WorldUnit.NOT_MOBILIZED).\
        exclude(status=unit.models.WorldUnit.REGROUPING).\
        exclude(battleunit__battle_side__battle__current=True)


def opponents_in_organization_list(organizations, tile):
    potential_conflicts = []

    input_list = list(organizations)
    while len(input_list):
        i = input_list.pop()
        for j in input_list:
            if i.get_region_stance_to(j, tile).get_stance() == organization.models.relationship.MilitaryStance.AGGRESSIVE:
                potential_conflicts.append([[i, ], [j, ]])
    return potential_conflicts


def add_allies(conflict, tile):
    for i, conflict_side in enumerate(conflict):
        other_conflict_side = conflict[0 if i == 1 else 1]
        for candidate in organizations_with_battle_ready_units(tile):
            if candidate in conflict_side or candidate in other_conflict_side:
                continue
            aggressive_to_all_in_other_side = True
            for state in other_conflict_side:
                stance = candidate.get_region_stance_to(state, tile).get_stance()
                if stance != organization.models.relationship.MilitaryStance.AGGRESSIVE:
                    aggressive_to_all_in_other_side = False
                    break
            aggressive_to_own_side = False
            for state in conflict_side:
                stance = candidate.get_region_stance_to(state, tile).get_stance()
                if stance == organization.models.relationship.MilitaryStance.AGGRESSIVE:
                    aggressive_to_own_side = True
                    break
            if aggressive_to_all_in_other_side and not aggressive_to_own_side:
                conflict[i].append(candidate)


def get_largest_conflict_in_list(conflicts, tile):
    result = None
    max_soldiers = 0
    for conflict in conflicts:
        soldiers = 0
        conflicting_states = conflict[0] + conflict[1]
        for unit in battle_ready_units_in_tile(tile):
            if unit.get_violence_monopoly() in conflicting_states:
                soldiers += unit.get_fighting_soldiers().count()
        if soldiers > max_soldiers:
            result = conflict
    return result


def create_battle_from_conflict(conflict, tile):
    battle = Battle.objects.create(
        tile=tile,
        current=True,
        start_turn=tile.world.current_turn
    )
    initialize_from_conflict(battle, conflict, tile)

    battle.tile.world.broadcast(
        'messaging/messages/battle_start.html',
        'battle',
        {'battle': battle},
        battle.get_absolute_url()
    )

    return battle


def battle_joins(battle: Battle):
    for candidate_unit in battle_ready_units_in_tile(battle.tile):
        candidate_vm = candidate_unit.get_violence_monopoly()
        try:
            battle_org = BattleOrganization.objects.get(
                side__battle=battle,
                organization=candidate_vm
            )
            add_unit_to_battle_in_progress(battle_org, candidate_unit)
        except BattleOrganization.DoesNotExist:
            sides = list(battle.battleside_set.all())
            for i, side in enumerate(sides):
                other_side = sides[0 if i == 1 else 1]
                aggressive_to_all_in_other_side = True
                for battle_state in other_side.battleorganization_set.all():
                    state = battle_state.organization
                    if candidate_vm.get_region_stance_to(state, battle.tile).get_stance() != organization.models.relationship.MilitaryStance.AGGRESSIVE:
                        aggressive_to_all_in_other_side = False
                        break
                aggressive_to_own_side = False
                for battle_state in side.battleorganization_set.all():
                    state = battle_state.organization
                    if candidate_vm.get_region_stance_to(state, battle.tile).get_stance() == organization.models.relationship.MilitaryStance.AGGRESSIVE:
                        aggressive_to_own_side = True
                        break
                if aggressive_to_all_in_other_side and not aggressive_to_own_side:
                    battle_org = BattleOrganization.objects.create(
                        side=side,
                        organization=candidate_vm
                    )
                    add_unit_to_battle_in_progress(battle_org, candidate_unit)
