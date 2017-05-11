import random

from django.db import transaction
from django.db.models.expressions import F

from battle.battle_init import initialize_from_conflict, start_battle
from battle.battle_tick import battle_turn
from battle.models import Battle
from messaging.helpers import send_notification_to_characters
from messaging.models import CharacterMessage
import world.models
import organization.models
import world.recruitment
from world.models import Building, Settlement, NPC


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
        self.battle_turns()
        self.trigger_battles()
        self.do_elections()
        self.do_conquests()
        self.do_barbarians()
        self.do_population_updates()
        self.do_job_updates()
        self.do_production()
        # self.do_trade()
        self.do_food_consumption()
        # self.do_food_spoilage()

        self.world.current_turn += 1
        self.world.save()

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
                pass
            elif settlement.guilds_setting == Settlement.GUILDS_RESTRICT:
                pass
            elif settlement.guilds_setting == Settlement.GUILDS_KEEP:
                pass
            elif settlement.guilds_setting == Settlement.GUILDS_PROMOTE:
                pass

    def do_population_updates(self):
        for settlement in Settlement.objects.filter(
            tile__world=self.world
        ):
            settlement.update_population()

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
        work_input = min(
            (ideal_workers / building.max_ideal_workers()) +
            (surplus_workers / building.max_surplus_workers()) * 0.5,
            1.5)
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
                # TODO add notification!
            else:
                message = character.perform_travel(character.travel_destination)
                character.travel_destination = None
                character.save()
                character.add_notification(CharacterMessage.TRAVEL, message)

    def restore_hours(self):
        for character in self.world.character_set.all():
            character.hours_in_turn_left = 15*24
            character.save()

    def trigger_battles(self):
        for tile in self.world.tile_set.all():
            trigger_battles_in_tile(tile)

    def battle_turns(self):
        for battle in Battle.objects.filter(tile__world=self.world, current=True):
            if not battle.started:
                start_battle(battle)
            battle_turn(battle)


def trigger_battles_in_tile(tile):
    conflicts = opponents_in_organization_list(
        organizations_with_battle_ready_units(tile),
        tile
    )
    conflict = get_largest_conflict_in_list(conflicts, tile)
    if conflict:
        return create_battle_from_conflict(conflict, tile)


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


def organizations_with_battle_ready_units(tile):
    result = []
    for unit in battle_ready_units_in_tile(tile):
        violence_monopoly = unit.get_violence_monopoly()
        if violence_monopoly and violence_monopoly not in result:
            result.append(violence_monopoly)
    return result


def battle_ready_units_in_tile(tile):
    return tile.get_units().exclude(status=world.models.WorldUnit.NOT_MOBILIZED).exclude(battleunit__battle_side__battle__current=True)


def opponents_in_organization_list(organizations, tile):
    potential_conflicts = []

    input_list = list(organizations)
    while len(input_list):
        i = input_list.pop()
        for j in input_list:
            if i.get_region_stance_to(j, tile).get_stance() == organization.models.MilitaryStance.AGGRESSIVE:
                potential_conflicts.append([i, j])
    return potential_conflicts


def get_largest_conflict_in_list(conflicts, tile):
    result = None
    max_soldiers = 0
    for conflict in conflicts:
        soldiers = 0
        for unit in battle_ready_units_in_tile(tile):
            if unit.get_violence_monopoly() in conflict:
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
    return battle
