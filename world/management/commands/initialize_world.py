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
                raise CommandError('World with id "%s" does not exist' % world_id)

            try:
                with perf_timer('World "%s" initialization' % world_id):
                    initialize_world(world)
            except AlreadyInitializedException:
                raise CommandError('World with id "%s" is already initialized' % world_id)

            self.stdout.write(self.style.SUCCESS('Successfully initialized world "%s"' % world_id))
