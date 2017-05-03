from django.test import TestCase
from django.urls.base import reverse

from battle.battle_init import initialize_from_conflict, start_battle
from battle.battle_tick import battle_tick
from battle.models import Battle, BattleCharacter, BattleUnit, BattleContubernium, BattleSoldier, BattleOrganization, \
    BattleContuberniumInTurn, BattleSoldierInTurn, BattleUnitInTurn, Order, OrderListElement
from organization.models import Organization
from world.initialization import initialize_unit
from world.models import Tile, WorldUnit, NPC
from world.turn import trigger_battles_in_tile


class MiscTests(TestCase):
    fixtures = ['simple_world']

    def test_conflict_creation_on_region_without_able_soldiers(self):
        tile = Tile.objects.get(id=108)
        trigger_battles_in_tile(tile)
        self.assertFalse(Battle.objects.exists())


class TestBattleStart(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 5}),
            follow=True
        )
        initialize_unit(WorldUnit.objects.get(id=1))
        initialize_unit(WorldUnit.objects.get(id=2))
        initialize_unit(WorldUnit.objects.get(id=3))
        tile = Tile.objects.get(id=108)
        self.battle = Battle.objects.create(tile=tile, start_turn=0)
        initialize_from_conflict(self.battle, [Organization.objects.get(id=105), Organization.objects.get(id=112)], tile)

    def test_battle_create_from_conflict(self):
        self.assertEqual(self.battle.battleside_set.count(), 2)

        self.assertTrue(BattleOrganization.objects.filter(side__battle=self.battle, organization=Organization.objects.get(id=105)).exists())
        self.assertTrue(BattleOrganization.objects.filter(side__battle=self.battle, organization=Organization.objects.get(id=112)).exists())
        self.assertEqual(BattleOrganization.objects.count(), 2)

        self.assertTrue(
            BattleOrganization.objects.get(organization_id=105).side.z !=
            BattleOrganization.objects.get(organization_id=112).side.z
        )

        self.assertTrue(BattleCharacter.objects.exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=Organization.objects.get(id=105),
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=Organization.objects.get(id=112),
        ).exists())
        self.assertEqual(BattleCharacter.objects.count(), 2)

        self.assertTrue(BattleUnit.objects.exists())
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=WorldUnit.objects.get(id=1), starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=WorldUnit.objects.get(id=2), starting_manpower=30).exists()
        )
        self.assertEqual(BattleUnit.objects.count(), 3)

        response = self.client.get(self.battle.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_start_battle(self):
        start_battle(self.battle)

        self.assertTrue(BattleContubernium.objects.exists())
        self.assertEqual(BattleContubernium.objects.count(), 16)
        self.assertTrue(BattleSoldier.objects.exists())
        self.assertEqual(BattleSoldier.objects.count(), 120)

        self.assertTrue(BattleContuberniumInTurn.objects.exists())
        self.assertEqual(BattleContuberniumInTurn.objects.count(), 16)
        self.assertTrue(BattleSoldierInTurn.objects.exists())
        self.assertEqual(BattleSoldierInTurn.objects.count(), 120)

        for npc in NPC.objects.all():
            self.assertTrue(BattleSoldier.objects.filter(world_npc=npc).exists())

        response = self.client.get(self.battle.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('battle:info', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('battle:battlefield_iframe', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            BattleUnitInTurn.objects.get(battle_turn=self.battle.get_latest_turn(), battle_unit__world_unit__id=2).order.what,
            Order.CHARGE
        )
        self.assertEqual(
            BattleUnitInTurn.objects.get(battle_turn=self.battle.get_latest_turn(), battle_unit__world_unit__id=1).order.what,
            Order.ADVANCE_IN_FORMATION
        )

    def test_battle_tick(self):
        start_battle(self.battle)

        battle_tick(self.battle)

        self.assertTrue(BattleContuberniumInTurn.objects.exists())
        self.assertEqual(BattleContuberniumInTurn.objects.count(), 16*2)
        self.assertTrue(BattleSoldierInTurn.objects.exists())
        self.assertEqual(BattleSoldierInTurn.objects.count(), 120*2)

        response = self.client.get(self.battle.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('battle:info', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('battle:battlefield_iframe', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            BattleUnitInTurn.objects.get(battle_turn=self.battle.get_latest_turn(), battle_unit__world_unit__id=2).order.what,
            Order.CHARGE
        )
        self.assertEqual(
            BattleUnitInTurn.objects.get(battle_turn=self.battle.get_latest_turn(), battle_unit__world_unit__id=1).order.what,
            Order.ADVANCE_IN_FORMATION
        )

        battle_tick(self.battle)

        self.assertTrue(BattleContuberniumInTurn.objects.exists())
        self.assertEqual(BattleContuberniumInTurn.objects.count(), 16*3)
        self.assertTrue(BattleSoldierInTurn.objects.exists())
        self.assertEqual(BattleSoldierInTurn.objects.count(), 120*3)

        response = self.client.get(self.battle.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('battle:info', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('battle:battlefield_iframe', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            BattleUnitInTurn.objects.get(battle_turn=self.battle.get_latest_turn(), battle_unit__world_unit__id=2).order.what,
            Order.CHARGE
        )
        self.assertEqual(
            BattleUnitInTurn.objects.get(battle_turn=self.battle.get_latest_turn(), battle_unit__world_unit__id=1).order.what,
            Order.ADVANCE_IN_FORMATION
        )

        self.assertEqual(self.battle.get_latest_turn().num, 2)

    def test_start_units_in_flank(self):

        unit1 = WorldUnit.objects.get(id=1)
        unit1.battle_side_pos = -4
        unit1.save()
        unit2 = WorldUnit.objects.get(id=2)
        unit2.battle_side_pos = 5
        unit2.save()
        unit3 = WorldUnit.objects.get(id=3)
        unit3.battle_side_pos = -5
        unit3.save()

        start_battle(self.battle)
