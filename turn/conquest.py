from messaging.helpers import send_notification_to_characters
from messaging.models import CharacterMessage
from unit.models import WorldUnit
from world.models.events import TileEvent
from world.models.geography import World


def worldwide_conquests(world: World):
    conquests_in_this_world = TileEvent.objects.filter(
        type=TileEvent.CONQUEST,
        active=True,
        tile__world=world
    )
    for conquest in conquests_in_this_world:
        present_mobilized_units = WorldUnit.objects\
            .filter(location__tile=conquest.tile)\
            .exclude(status=WorldUnit.NOT_MOBILIZED)
        conquering_units = []
        defending_units = []
        for present_mobilized_unit in present_mobilized_units:
            if present_mobilized_unit.get_violence_monopoly() == conquest.organization:
                conquering_units.append(present_mobilized_unit)
            if present_mobilized_unit.get_violence_monopoly() == conquest.tile.controlled_by.get_violence_monopoly():
                defending_units.append(present_mobilized_unit)

        # stop conquest if no more units present
        if len(conquering_units) == 0:
            conquest.end_turn = world.current_turn
            conquest.active = False
            conquest.save()
            continue

        # decrease counter
        for defending_unit in defending_units:
            conquest.counter -= defending_unit.get_fighting_soldiers().count()
        if conquest.counter < 0:
            conquest.counter = 0

        # if counter is larger than population, conquer
        if conquest.counter > conquest.tile.get_total_population():
            previous_owner = conquest.tile.controlled_by.get_violence_monopoly()
            conquest.tile.controlled_by = conquest.organization
            conquest.end_turn = world.current_turn
            conquest.active = False
            conquest.tile.save()
            conquest.save()
            send_notification_to_characters(
                world.character_set,
                'messaging/messages/conquest_success.html',
                CharacterMessage.CONQUEST,
                {
                    'tile_event': conquest,
                    'previous_owner': previous_owner
                }
            )
