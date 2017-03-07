from django.db import transaction


class TurnProcessor:
    def __init__(self, world):
        self.world =world

    @transaction.atomic
    def do_turn(self):
        self.do_travels()
        self.restore_hours()

    def do_travels(self):
        for character in self.world.character_set.all():

            if character.travel_destination is None:
                continue

            travel_check = character.check_travelability(character.travel_destination)
            if travel_check is not None:
                pass
                #TODO add notification!
            else:
                character.hours_in_turn_left -= character.travel_time(character.travel_destination)
                character.location = character.travel_destination
                character.travel_destination = None
                character.save()
                #TODO add notification!

    def restore_hours(self):
        for character in self.world.character_set.all():
            character.hours_in_turn_left = 15*24
            character.save()
