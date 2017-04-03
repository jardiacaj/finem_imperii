from django.test import TestCase

from organization.models import Organization
from world.models import Tile, WorldUnit
from world.turn import organizations_with_battle_ready_units, battle_ready_units_in_tile, opponents_in_organization_list


class TestTurn(TestCase):
    fixtures = ['simple_world']

    def test_organizations_with_battle_ready_units(self):
        tile = Tile.objects.get(id=108)
        result = organizations_with_battle_ready_units(tile)
        self.assertIn(Organization.objects.get(id=105), result)
        self.assertIn(Organization.objects.get(id=112), result)
        self.assertEqual(len(result), 2)

    def test_battle_ready_units_in_tile(self):
        tile = Tile.objects.get(id=108)
        result = battle_ready_units_in_tile(tile)
        self.assertIn(WorldUnit.objects.get(id=1), result)
        self.assertIn(WorldUnit.objects.get(id=2), result)
        self.assertEqual(len(result), 2)

    def test_opponents_in_organization_list(self):
        tile = Tile.objects.get(id=108)
        result = opponents_in_organization_list(organizations_with_battle_ready_units(tile), tile)
        self.assertEqual(len(result), 1)
        opponents = result[0]
        self.assertIn(Organization.objects.get(id=105), opponents)
        self.assertIn(Organization.objects.get(id=112), opponents)
        self.assertEqual(len(opponents), 2)
