from django.test import TestCase

import world.initialization
from organization.models import Organization, PositionElection
from world.initialization import initialize_world
from world.models import WorldUnit, Settlement, World


class TestInitialization(TestCase):
    fixtures = ['simple_world']

    def test_initialize_unit(self):
        unit = WorldUnit.objects.get(id=1)
        world.initialization.initialize_unit(unit)
        self.assertEqual(unit.soldier.count(), 30)

    def test_initialize_settlement(self):
        settlement = Settlement.objects.get(id=1007)
        world.initialization.initialize_settlement(settlement)
        self.assertEqual(settlement.npc_set.count(), settlement.population)

    def test_initialize_organization_elected(self):
        organization = Organization.objects.get(name="Democracy leader")
        organization.character_members.clear()
        world.initialization.initialize_organization(organization)
        self.assertTrue(PositionElection.objects.filter(position=organization, closed=False).exists())

    def test_initialize_organization_inherited(self):
        organization = Organization.objects.get(name="Small King")
        organization.character_members.clear()
        world.initialization.initialize_organization(organization)
        self.assertFalse(PositionElection.objects.filter(position=organization, closed=False).exists())

    def test_world_initialization(self):
        initialize_world(World.objects.get(id=2))


class TestEmortuusInitialization(TestCase):
    fixtures = ['world1']

    def test_initialization(self):
        initialize_world(World.objects.get(id=1))
