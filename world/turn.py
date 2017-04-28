from django.db import transaction

from battle.battle_init import initialize_from_conflict, start_battle
from battle.battle_tick import battle_turn
from battle.models import Battle
from messaging.helpers import send_notification_to_characters
from messaging.models import CharacterMessage
import world.models
import organization.models

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November',
          'December']


def turn_to_date(turn):
    return "{} {} I.E.".format(months[turn % 12], turn//12 + 815)


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

        self.world.current_turn += 1
        self.world.save()

    def do_conquests(self):
        conquests_in_this_world = world.models.TileEvent.objects.filter(
            type=world.models.TileEvent.CONQUEST,
            end_turn__isnull=True,
            tile__world=self.world
        )
        for conquest in conquests_in_this_world:
            present_movilized_units = world.models.WorldUnit.objects\
                .filter(location__tile=conquest.tile)\
                .exclude(status=world.models.WorldUnit.NOT_MOBILIZED)
            conquering_units = []
            defending_units = []
            for unit in present_movilized_units:
                if unit.owner_character.get_violence_monopoly() == conquest.organization:
                    conquering_units.append(unit)
                if unit.owner_character.get_violence_monopoly() == conquest.tile.controlled_by.get_violence_monopoly():
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
            tile.trigger_battles()

    def battle_turns(self):
        for battle in Battle.objects.filter(tile__world=self.world, current=True):
            if not battle.started:
                start_battle(battle)
            battle_turn(battle)


def organizations_with_battle_ready_units(tile):
    result = []
    for unit in battle_ready_units_in_tile(tile):
        violence_monopoly = unit.owner_character.get_violence_monopoly()
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
            if unit.owner_character.get_violence_monopoly() in conflict:
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
