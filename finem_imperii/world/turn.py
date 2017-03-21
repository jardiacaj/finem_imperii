from django.db import transaction

from messaging.models import CharacterNotification

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

        self.world.current_turn += 1
        self.world.save()

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
                character.add_notification(CharacterNotification.TRAVEL, message)

    def restore_hours(self):
        for character in self.world.character_set.all():
            character.hours_in_turn_left = 15*24
            character.save()
