from django.test import TestCase

from world.initialization import WorldInitializer
from world.models import WorldUnit


class TestInitialization(TestCase):
    fixtures = ['simple_world']

    def test_initialize_unit(self):
        unit = WorldUnit.objects.get(id=1)
        initializer = WorldInitializer(world=unit.world)
        initializer.initialize_unit(unit)
        self.assertEqual(unit.soldier.count(), 30)