from django.core.management.base import BaseCommand, CommandError

from context_managers import perf_timer
from world.models import World
from world.turn import pass_turn


class Command(BaseCommand):
    help = 'Passes a turn in the specified world'

    def add_arguments(self, parser):
        parser.add_argument('world_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for world_id in options['world_id']:
            try:
                world = World.objects.get(pk=world_id)
            except World.DoesNotExist:
                raise CommandError('World with id "%s" does not exist' % world_id)

            with perf_timer('World "%s" turn' % world_id):
                pass_turn(world)

            self.stdout.write(self.style.SUCCESS('Passed turn in world "%s"' % world_id))
