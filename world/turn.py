import random

import math
from django.db import transaction
from django.db.models.expressions import F

from battle.battle_init import initialize_from_conflict, start_battle, \
    add_unit_to_battle_in_progress
from battle.battle_tick import battle_turn
from battle.models import Battle, BattleOrganization
from messaging.helpers import send_notification_to_characters
from messaging.models import CharacterMessage
import world.models
import organization.models
import world.recruitment
import world.initialization
from world.models import Building, Settlement, NPC, WorldUnit
from world.templatetags.extra_filters import nice_turn


def pass_turn(world):
    world.blocked_for_turn = True
    world.save()
    turn_processor = TurnProcessor(world)
    turn_processor.do_turn()
    world.blocked_for_turn = False
    world.save()


field_input_months = (0, 1, 2, 3, 4, 5, 8, 9, 10, 11)
field_output_months = (4, 5, 6, 7, 8)
field_output_multipliers = {4: 0.5, 5: 1, 6: 0.5, 7: 1, 8: 0.5}
field_production_reset_month = 8


class TurnProcessor:
    def __init__(self, world):
        self.world = world

    @transaction.atomic
    def do_turn(self):
        self.do_travels()
        self.restore_hours()
        self.do_unit_maintenance()
        self.battle_joins()
        self.battle_turns()
        self.trigger_battles()
        self.do_elections()
        self.do_conquests()
        self.do_barbarians()
        # self.do_residence_assignment()
        self.do_job_updates()
        self.do_production()
        # self.do_trade()
        self.do_food_consumption()
        self.do_population_changes()
        # self.do_food_spoilage()
        self.do_taxes()

        self.world.current_turn += 1
        self.world.save()

        self.world.broadcast(
            "It is now {}.".format(nice_turn(self.world.current_turn)),
            'turn'
        )

    def do_population_changes(self):
        for tile in self.world.tile_set.all():
            for settlement in tile.settlement_set.all():
                self.do_settlement_population_changes(settlement)

    def do_settlement_population_changes(self, settlement):
        settlement.update_population()
        amount_to_generate = 0

        if settlement.population < 50:
            amount_to_generate += 5

        if (
                settlement.population < settlement.population_default and
                settlement.get_hunger_percentage() < 3
        ):
            amount_to_generate += int(settlement.population * 0.05)

        residences = settlement.building_set.filter(
            type=Building.RESIDENCE).all()
        for i in range(amount_to_generate):
            world.initialization.generate_npc(i, residences, settlement)
        if amount_to_generate > 0:
            settlement.update_population()

    def do_unit_maintenance(self):
        for unit in self.world.worldunit_set.all():
            if unit.status == WorldUnit.REGROUPING:
                if (
                        unit.owner_character is not None and
                        unit.location == unit.owner_character.location):
                    unit.status = WorldUnit.FOLLOWING
                else:
                    unit.status = WorldUnit.STANDING
                unit.save()

            if unit.owner_character and unit.status != WorldUnit.NOT_MOBILIZED:
                cost = unit.soldier.count()
                if unit.owner_character.cash < unit.monthly_cost():
                    unit.demobilize()
                    unit.owner_character.add_notification(
                        'unit',
                        "You don't have the {} coins your unit {} demands as"
                        "payment. It has demobilized.".format(
                            unit.monthly_cost(),
                            unit,
                            unit.owner_character.save()
                        )
                    )
                else:
                    unit.owner_character.cash -= unit.monthly_cost()
                    unit.owner_character.save()
                    unit.owner_character.add_notification(
                        'unit',
                        'You paid {} coins to your unit {}. You now have '
                        '{} coins left.'.format(
                            unit.monthly_cost(),
                            unit,
                            unit.owner_character.save()
                        )
                    )

    def do_taxes(self):
        for state in self.world.get_violence_monopolies():
            state.tax_countdown -= 1
            state.save()
            if state.tax_countdown <= 0:
                self.do_state_taxes(state)
                state.tax_countdown = 12
                state.save()

    def do_state_taxes(self, state: organization.models.Organization):
        settlement_input = []
        total_input = 0
        for tile in state.get_all_controlled_tiles():
            for settlement in tile.settlement_set.all():
                t = 0
                for guild in settlement.building_set.filter(
                        type=Building.GUILD):
                    t += guild.field_production_counter
                    total_input += guild.field_production_counter
                    guild.field_production_counter = 0
                    guild.save()

                settlement_input.append(
                    (settlement, t)
                )

        member_share = math.floor(
            total_input / state.character_members.count()
        )
        for member in state.character_members.all():
            member.cash += member_share
            member.save()

    def do_job_updates(self):
        for settlement in Settlement.objects.filter(
            tile__world=self.world
        ):
            self.do_settlement_job_updates(settlement)

    def do_settlement_job_updates(self, settlement: Settlement):
        settlement.get_residents().filter(able=False).update(workplace=None)
        npcs_looking_for_a_job = settlement.get_residents().filter(
            workplace=None,
            age_months__gt=NPC.VERY_YOUNG_AGE_LIMIT
        )
        fields = list(settlement.building_set.filter(
            type=Building.GRAIN_FIELD,
            owner=None
        ))
        for jobseeker in npcs_looking_for_a_job:
            jobseeker.workplace = random.choice(fields)
            jobseeker.save()

        if not settlement.tile.controlled_by.get_violence_monopoly().barbaric:
            if settlement.guilds_setting == Settlement.GUILDS_PROHIBIT:
                settlement.get_residents()
            elif settlement.guilds_setting == Settlement.GUILDS_RESTRICT:
                pass
            elif settlement.guilds_setting == Settlement.GUILDS_KEEP:
                pass
            elif settlement.guilds_setting == Settlement.GUILDS_PROMOTE:
                pass

    def do_food_consumption(self):
        for settlement in Settlement.objects.filter(
            tile__world=self.world
        ):
            self.do_settlement_food_consumption(settlement)

    def do_settlement_food_consumption(self, settlement: Settlement):
        mouths = settlement.population
        granary = settlement.get_default_granary()
        bushels_to_consume = min(
            mouths,
            granary.population_consumable_bushels()
        )
        granary.consume_bushels(bushels_to_consume)

        hunger = mouths - bushels_to_consume
        if hunger > 0 and settlement.npc_set.exists():
            for npc in random.sample(list(settlement.npc_set.all()), hunger):
                npc.hunger += 1
                npc.save()

        if hunger == 0 and settlement.npc_set.filter(hunger__gt=0).exists():
            settlement.npc_set.filter(hunger__gt=0).update(
                hunger=F('hunger')-1
            )

        for npc in settlement.npc_set.filter(hunger__gt=3):
            if random.getrandbits(3) == 0:
                npc.take_hit()
            if npc.hunger > 5:
                npc.take_hit()

        settlement.update_population()

    def do_production(self):
        for building in Building.objects.filter(
                settlement__tile__world=self.world):
            self.do_building_production(building)

    def do_building_production(self, building: Building):
        workers = building.worker
        ideal_workers = min(building.max_ideal_workers(), workers.count())
        surplus_workers = max(
            0,
            workers.count() - building.max_ideal_workers()
        )

        work_input = 0
        if building.max_ideal_workers():
            work_input += min(
                (ideal_workers / building.max_ideal_workers()),
                1)
        if building.max_surplus_workers():
            work_input += min(
                (surplus_workers / building.max_surplus_workers()) * 0.5,
                0.5)

        if building.type == Building.GRAIN_FIELD and building.level > 0:
            current_month = self.world.current_turn % 12

            if current_month in field_output_months and work_input > 0:
                time_portion = \
                    field_output_multipliers[current_month] / \
                    sum(field_output_multipliers.values())
                production_counter_remove = min(
                    work_input * time_portion * 1000,
                    building.field_production_counter
                )
                building.field_production_counter -= production_counter_remove
                building.save()
                bushel_output = (
                    building.quantity
                    * production_counter_remove / 1000
                    * 2.4
                )
                building.settlement.get_default_granary().add_bushels(
                    round(bushel_output)
                )

            if current_month == field_production_reset_month:
                building.field_production_counter = 0
                building.save()

            if current_month in field_input_months and work_input > 0:
                time_portion = 1 / len(field_input_months)
                production_counter_add = work_input * time_portion * 1000
                building.field_production_counter += production_counter_add
                building.save()

        if building.type == Building.GUILD:
            building.field_production_counter *= 0.9
            building.field_production_counter += workers.count()
            building.save()

    def do_barbarians(self):
        world_settlements = world.models.Settlement.objects.filter(
            tile__world=self.world
        )
        for settlement in world_settlements:
            do_settlement_barbarians(settlement)

    def do_conquests(self):
        conquests_in_this_world = world.models.TileEvent.objects.filter(
            type=world.models.TileEvent.CONQUEST,
            end_turn__isnull=True,
            tile__world=self.world
        )
        for conquest in conquests_in_this_world:
            present_mobilized_units = world.models.WorldUnit.objects\
                .filter(location__tile=conquest.tile)\
                .exclude(status=world.models.WorldUnit.NOT_MOBILIZED)
            conquering_units = []
            defending_units = []
            for unit in present_mobilized_units:
                if unit.get_violence_monopoly() == conquest.organization:
                    conquering_units.append(unit)
                if unit.get_violence_monopoly() == conquest.tile.controlled_by.get_violence_monopoly():
                    defending_units.append(unit)

            # stop conquest if no more units present
            if len(conquering_units) == 0:
                conquest.end_turn = self.world.current_turn
                conquest.save()
                continue

            # decrease counter
            for unit in defending_units:
                conquest.counter -= unit.get_fighting_soldiers().count()
            if conquest.counter < 0:
                conquest.counter = 0

            # if counter is larger than population, conquer
            if conquest.counter > conquest.tile.get_total_population():
                previous_owner = conquest.tile.controlled_by.get_violence_monopoly()
                conquest.tile.controlled_by = conquest.organization
                conquest.end_turn = self.world.current_turn
                conquest.tile.save()
                conquest.save()
                send_notification_to_characters(
                    self.world.character_set,
                    CharacterMessage.CONQUEST,
                    "{tile}, which was previously controlled by {previous}, has been conquered by {conqueror}!".format(
                        tile=conquest.tile.get_html_link(),
                        previous=previous_owner.get_html_link(),
                        conqueror=conquest.organization.get_html_link()
                    ),
                    True
                )

    def do_elections(self):
        for organization in self.world.organization_set.all():
            if organization.current_election and organization.current_election.turn == self.world.current_turn:
                organization.current_election.resolve()

        for organization in self.world.organization_set.all():
            if organization.election_period_months and not organization.current_election and not organization.last_election:
                organization.convoke_elections(12)
            elif organization.election_period_months and not organization.current_election and organization.last_election:
                turns_since_last_election = self.world.current_turn - organization.last_election.turn
                turns_to_next_election = organization.election_period_months - turns_since_last_election
                if turns_to_next_election < 12:
                    organization.convoke_elections(12)

    def do_travels(self):
        for character in self.world.character_set.all():

            if character.travel_destination is None:
                continue

            travel_check = character.check_travelability(character.travel_destination)
            if travel_check is not None:
                pass
            else:
                message = character.perform_travel(character.travel_destination)
                character.add_notification(CharacterMessage.TRAVEL, message)
            character.travel_destination = None
            character.save()

    def restore_hours(self):
        for character in self.world.character_set.all():
            character.hours_in_turn_left = 15*24
            if character.get_battle_participating_in() is not None:
                character.add_notification(
                    'battle',
                    "Because you are taking part in a battle, you only "
                    "have half as much time available."
                )
                character.hours_in_turn_left /= 2
            character.save()

    def trigger_battles(self):
        for tile in self.world.tile_set.all():
            if not Battle.objects.filter(
                    tile=tile,
                    end_turn=self.world.current_turn).exists():
                trigger_battles_in_tile(tile)

    def battle_joins(self):
        for battle in Battle.objects.filter(
                tile__world=self.world, current=True
        ):
            battle_joins(battle)

    def battle_turns(self):
        for battle in Battle.objects.filter(
                tile__world=self.world, current=True
        ):
            if not battle.started:
                start_battle(battle)
            battle_turn(battle)


def do_settlement_barbarians(settlement):
    pure_barbarian_units = world.models.WorldUnit.objects.filter(
        location=settlement,
        owner_character__isnull=True
    )
    non_pure_barbarian_units = world.models.WorldUnit.objects.filter(
        location=settlement,
        owner_character__isnull=False
    )
    non_pure_barbarian_soldiers = sum(
        [unit.soldier.count() for unit in non_pure_barbarian_units]
    )
    if non_pure_barbarian_soldiers < settlement.population / 10:
        barbarian_soldiers = sum(
            [unit.soldier.count() for unit in pure_barbarian_units]
        )
        if barbarian_soldiers >= settlement.population / 3:
            return
        if settlement.population < 20:
            return
        recruitment_size = random.randrange(10, settlement.population // 3)
        soldiers = world.recruitment.sample_candidates(
            world.recruitment.all_recruitable_soldiers_in_settlement(settlement),
            recruitment_size
        )
        world.recruitment.recruit_unit(
            "Barbarians of {}".format(settlement),
            None,
            settlement,
            soldiers,
            world.models.WorldUnit.CONSCRIPTION,
            world.models.WorldUnit.INFANTRY
        )


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


def organizations_with_battle_ready_units(tile):
    result = []
    for unit in battle_ready_units_in_tile(tile):
        violence_monopoly = unit.get_violence_monopoly()
        if violence_monopoly and violence_monopoly not in result:
            result.append(violence_monopoly)
    return result


def battle_ready_units_in_tile(tile):
    return tile.get_units().\
        exclude(status=world.models.WorldUnit.NOT_MOBILIZED).\
        exclude(status=world.models.WorldUnit.REGROUPING).\
        exclude(battleunit__battle_side__battle__current=True)


def opponents_in_organization_list(organizations, tile):
    potential_conflicts = []

    input_list = list(organizations)
    while len(input_list):
        i = input_list.pop()
        for j in input_list:
            if i.get_region_stance_to(j, tile).get_stance() == organization.models.MilitaryStance.AGGRESSIVE:
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
                if stance != organization.models.MilitaryStance.AGGRESSIVE:
                    aggressive_to_all_in_other_side = False
                    break
            aggressive_to_own_side = False
            for state in conflict_side:
                stance = candidate.get_region_stance_to(state, tile).get_stance()
                if stance == organization.models.MilitaryStance.AGGRESSIVE:
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
        "A battle has started in {}".format(battle.tile),
        'battle',
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
                    if candidate_vm.get_region_stance_to(state, battle.tile).get_stance() != organization.models.MilitaryStance.AGGRESSIVE:
                        aggressive_to_all_in_other_side = False
                        break
                aggressive_to_own_side = False
                for battle_state in side.battleorganization_set.all():
                    state = battle_state.organization
                    if candidate_vm.get_region_stance_to(state, battle.tile).get_stance() == organization.models.MilitaryStance.AGGRESSIVE:
                        aggressive_to_own_side = True
                        break
                if aggressive_to_all_in_other_side and not aggressive_to_own_side:
                    battle_org = BattleOrganization.objects.create(
                        side=side,
                        organization=candidate_vm
                    )
                    add_unit_to_battle_in_progress(battle_org, candidate_unit)
