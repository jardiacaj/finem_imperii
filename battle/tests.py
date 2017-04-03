from django.test import TestCase

from battle.models import Battle
from organization.models import Organization
from world.models import Tile


class TestBattleStart(TestCase):
    fixtures = ['simple_world']

    def test_battle_create_from_conflict(self):
        tile = Tile.objects.get(id=108)
        battle = Battle.objects.create(tile=tile)
        battle.initialize_from_conflict([Organization.objects.get(id=105), Organization.objects.get(id=112)], tile)

        self.assertTrue(battle.battleorganization_set.filter(organization=Organization.objects.get(id=105)).exists())
        self.assertTrue(battle.battleorganization_set.filter(organization=Organization.objects.get(id=112)).exists())

        self.assertTrue(
            battle.battleorganization_set.get(organization_id=105).z !=
            battle.battleorganization_set.get(organization_id=112).z
        )
