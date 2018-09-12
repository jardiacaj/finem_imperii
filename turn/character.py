from character.models import Character
from messaging.models import CharacterMessage
from world.models.geography import World


def worldwide_pause_characters(world: World):
    for character in world.character_set.filter(paused=False):
        character.maybe_pause_for_inactivity()


def worldwide_character_travels(world: World):
    for character in world.character_set.all():
        do_character_travel(character)


def do_character_travel(character: Character):
    if character.travel_destination is not None:
        travel_check = character.check_travelability(
            character.travel_destination)
        if travel_check is not None:
            pass
        else:
            travel_time, destination = character.perform_travel(
                character.travel_destination)
            character.add_notification(
                'messaging/messages/travel.html',
                'You arrive to {}'.format(destination.name),
                {
                    'travel_time': travel_time,
                    'destination': destination
                }
            )
        character.travel_destination = None
        character.save()


def worldwide_restore_character_hours(world: World):
    for character in world.character_set.all():
        restore_character_hours(character)


def restore_character_hours(character: Character):
    character.hours_in_turn_left = 15*24
    if character.get_battle_participating_in() is not None:
        character.hours_in_turn_left /= 2
    character.save()
