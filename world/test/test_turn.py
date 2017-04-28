from django.test import TestCase
from django.urls.base import reverse

from battle.models import Battle
from organization.models import Organization
from world.admin import pass_turn
from world.initialization import initialize_unit
from world.models import Tile, WorldUnit, World
from world.turn import organizations_with_battle_ready_units, battle_ready_units_in_tile, \
    opponents_in_organization_list, get_largest_conflict_in_list, create_battle_from_conflict


class TestTurn(TestCase):
    fixtures = ['simple_world']

    def test_pass_turn_admin_action(self):
        pass_turn(None, None, World.objects.all())

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
        self.assertEqual(len(result), 3)

    def test_opponents_in_organization_list(self):
        tile = Tile.objects.get(id=108)
        result = opponents_in_organization_list(organizations_with_battle_ready_units(tile), tile)
        self.assertEqual(len(result), 1)
        opponents = result[0]
        self.assertIn(Organization.objects.get(id=105), opponents)
        self.assertIn(Organization.objects.get(id=112), opponents)
        self.assertEqual(len(opponents), 2)

    def test_get_largest_conflict_in_list(self):
        initialize_unit(WorldUnit.objects.get(id=1))
        initialize_unit(WorldUnit.objects.get(id=2))
        tile = Tile.objects.get(id=108)
        conflicts = opponents_in_organization_list(organizations_with_battle_ready_units(tile), tile)
        result = get_largest_conflict_in_list(conflicts, tile)
        self.assertEqual(len(result), 2)
        self.assertIn(Organization.objects.get(id=105), result)
        self.assertIn(Organization.objects.get(id=112), result)
        self.assertEqual(len(result), 2)

    def test_create_battle_from_conflict(self):
        initialize_unit(WorldUnit.objects.get(id=1))
        initialize_unit(WorldUnit.objects.get(id=2))
        tile = Tile.objects.get(id=108)
        organization1 = Organization.objects.get(id=105)
        organization2 = Organization.objects.get(id=112)

        battle = create_battle_from_conflict([organization1, organization2], tile)
        self.assertEqual(battle.tile, tile)

    def test_create_only_one_conflict(self):
        world = World.objects.get(id=2)
        for unit in WorldUnit.objects.filter(world=world):
            initialize_unit(unit)
        pass_turn(None, None, World.objects.filter(id=2))
        pass_turn(None, None, World.objects.filter(id=2))
        self.assertEqual(Battle.objects.count(), 1)
        Battle.objects.filter(tile__world=world).update(current=False)
        pass_turn(None, None, World.objects.filter(id=2))
        self.assertEqual(Battle.objects.count(), 2)

    def test_world_blocking(self):
        world = World.objects.get(id=2)
        world.blocked_for_turn = True
        world.save()

        response = self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 3}),
            follow=True
        )
        self.assertRedirects(response, reverse('account:home'))
