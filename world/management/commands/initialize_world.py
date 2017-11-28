from django.core.management.base import BaseCommand, CommandError

from context_managers import perf_timer
from world.initialization import initialize_world, AlreadyInitializedException
from world.models.geography import World


class Command(BaseCommand):
    help = 'Initializes the specified world'

    def add_arguments(self, parser):
        parser.add_argument('world_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for world_id in options['world_id']:
            try:
                world = World.objects.get(pk=world_id)
            except World.DoesNotExist:
                raise CommandError(
                    'World with id {} does not exist'.format(world_id))

            try:
                with perf_timer('{} initialization'.format(world)):
                    initialize_world(world)
            except AlreadyInitializedException:
                raise CommandError('{} is already initialized'.format(world))

            self.stdout.write(
                self.style.SUCCESS('Successfully initialized {}'.format(world))
            )
