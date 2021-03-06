import logging

from django.core.management.base import BaseCommand, CommandError

from turn.turn import pass_turn
from world.models.geography import World


class Command(BaseCommand):
    help = 'Passes a turn in the specified world'

    def add_arguments(self, parser):
        parser.add_argument('world_id', nargs='+', type=int)

    def handle(self, *args, **options):
        logging.getLogger().setLevel(logging.INFO)

        for world_id in options['world_id']:
            try:
                world = World.objects.get(pk=world_id)
            except World.DoesNotExist:
                raise CommandError('World with id {} does not exist'.format(
                    world_id
                ))

            pass_turn(world)

            self.stdout.write(
                self.style.SUCCESS(
                    'Passed turn in {} ({})'.format(
                        world,
                        world_id
                    )
                )
            )
