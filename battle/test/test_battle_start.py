from django.test import TestCase
from django.urls.base import reverse

from battle.battle_init import initialize_from_conflict, start_battle
from battle.battle_tick import battle_tick
from battle.models import Battle, BattleCharacter, BattleUnit, \
    BattleContubernium, BattleSoldier, BattleOrganization, \
    BattleContuberniumInTurn, BattleSoldierInTurn, BattleUnitInTurn, Order
from organization.models.organization import Organization
from organization.models.relationship import MilitaryStance
from turn.barbarians import generate_barbarian_unit
from turn.battle import trigger_battles_in_tile, battle_joins, \
    worldwide_trigger_battles, worldwide_battle_joins
from unit.models import WorldUnit
from world.initialization import initialize_unit, initialize_settlement
from world.models.geography import Tile, World, Settlement
from world.models.npcs import NPC


class MiscTests(TestCase):
    fixtures = ['simple_world']

    def test_conflict_creation_on_region_without_able_soldiers(self):
        tile = Tile.objects.get(id=108)
        trigger_battles_in_tile(tile)
        self.assertFalse(Battle.objects.exists())


class BattleBarbarians(TestCase):
    fixtures = ['simple_world']

    def test_battle_with_barbarians(self):
        world = World.objects.get(id=2)
        unit_of_kingrom_member = WorldUnit.objects.get(id=4)
        initialize_unit(unit_of_kingrom_member)
        kingdom_member = unit_of_kingrom_member.owner_character
        settlement = kingdom_member.location
        initialize_settlement(settlement)
        generate_barbarian_unit(30, settlement)
        worldwide_trigger_battles(world)
        self.assertTrue(settlement.tile.get_current_battles().exists())
        battle = settlement.tile.get_current_battles()[0]
        start_battle(battle)
        battle_tick(battle)
        generate_barbarian_unit(30, settlement)
        battle_joins(battle)
        battle_tick(battle)


class TestBattleStart(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 5}),
            follow=True
        )
        initialize_unit(WorldUnit.objects.get(id=1))
        initialize_unit(WorldUnit.objects.get(id=2))
        initialize_unit(WorldUnit.objects.get(id=3))
        tile = Tile.objects.get(id=108)
        self.battle = Battle.objects.create(tile=tile, start_turn=0)
        initialize_from_conflict(
            self.battle,
            [
                [Organization.objects.get(id=105)],
                [Organization.objects.get(id=112)]
            ],
            tile
        )

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

    def test_manpower(self):
        start_battle(self.battle)

        side0 = self.battle.battleside_set.get(z=False)
        self.assertEqual(side0.get_manpower(), 30)
        self.assertEqual(side0.get_proportional_strength(), 1/3)
        side1 = self.battle.battleside_set.get(z=True)
        self.assertEqual(side1.get_manpower(), 90)
        self.assertEqual(side1.get_proportional_strength(), 3)


class TestBattleStartWithAllies(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 5}),
            follow=True
        )
        self.tile = Tile.objects.get(id=108)
        self.unit_of_warrior = WorldUnit.objects.get(id=1)
        initialize_unit(self.unit_of_warrior)
        self.unit_of_commonwealth = WorldUnit.objects.get(id=2)
        initialize_unit(self.unit_of_commonwealth)
        self.unit_of_warrior2 = WorldUnit.objects.get(id=3)
        initialize_unit(self.unit_of_warrior2)
        self.unit_of_kingdom = WorldUnit.objects.get(id=4)
        self.unit_of_kingdom.location = Settlement.objects.get(id=1007)
        self.unit_of_kingdom.save()
        initialize_unit(self.unit_of_kingdom)

        self.kingdom = Organization.objects.get(id=101)
        self.commonwealth = Organization.objects.get(id=105)
        self.horde = Organization.objects.get(id=112)

        stance = self.kingdom.get_region_stance_to(self.horde, self.tile)
        stance.stance_type = MilitaryStance.AGGRESSIVE
        stance.save()
        stance = self.commonwealth.get_region_stance_to(self.horde, self.tile)
        stance.stance_type = MilitaryStance.AGGRESSIVE
        stance.save()

    def test_battle_create_from_conflict_with_allies(self):
        self.battle = Battle.objects.create(tile=self.tile, start_turn=0)
        initialize_from_conflict(
            self.battle,
            [
                [self.commonwealth, self.kingdom],
                [self.horde]
            ],
            self.tile
        )

        self.assertEqual(self.battle.battleside_set.count(), 2)

        self.assertTrue(BattleOrganization.objects.filter(side__battle=self.battle, organization=self.kingdom).exists())
        self.assertTrue(BattleOrganization.objects.filter(side__battle=self.battle, organization=self.horde).exists())
        self.assertTrue(BattleOrganization.objects.filter(side__battle=self.battle, organization=self.commonwealth).exists())
        self.assertEqual(BattleOrganization.objects.count(), 3)

        self.assertTrue(
            BattleOrganization.objects.get(organization=self.kingdom).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )
        self.assertTrue(
            BattleOrganization.objects.get(organization=self.commonwealth).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )

        self.assertTrue(BattleCharacter.objects.exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.kingdom,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.horde,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.commonwealth,
        ).exists())
        self.assertEqual(BattleCharacter.objects.count(), 3)

        self.assertEqual(
            self.unit_of_kingdom.owner_character.get_battle_participating_in(),
            self.battle
        )

        self.assertTrue(BattleUnit.objects.exists())
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior, starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_commonwealth, starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior2, starting_manpower=60).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_kingdom, starting_manpower=100).exists()
        )
        self.assertEqual(BattleUnit.objects.count(), 4)

        response = self.client.get(self.battle.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_battle_create_from_units_with_allies(self):
        world = World.objects.get(id=2)
        worldwide_trigger_battles(world)

        self.assertTrue(Battle.objects.exists())

        self.battle = Battle.objects.get(id=1)

        self.assertEqual(self.battle.battleside_set.count(), 2)

        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.kingdom).exists())
        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.horde).exists())
        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.commonwealth).exists())
        self.assertEqual(BattleOrganization.objects.count(), 3)

        self.assertTrue(
            BattleOrganization.objects.get(organization=self.kingdom).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )
        self.assertTrue(
            BattleOrganization.objects.get(
                organization=self.commonwealth).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )

        self.assertTrue(BattleCharacter.objects.exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.kingdom,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.horde,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.commonwealth,
        ).exists())
        self.assertEqual(BattleCharacter.objects.count(), 3)

        self.assertTrue(BattleUnit.objects.exists())
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_commonwealth,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior2,
                                      starting_manpower=60).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_kingdom,
                                      starting_manpower=100).exists()
        )
        self.assertEqual(BattleUnit.objects.count(), 4)

        response = self.client.get(self.battle.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)

        start_battle(self.battle)
        battle_tick(self.battle)

    def test_battle_create_from_units_with_allies_joining_during_battle1(self):
        self.unit_of_warrior.location_id = 1001
        self.unit_of_warrior.save()

        world = World.objects.get(id=2)
        worldwide_trigger_battles(world)

        self.assertTrue(Battle.objects.exists())

        self.battle = Battle.objects.get(id=1)

        self.assertEqual(self.battle.battleside_set.count(), 2)

        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.kingdom).exists())
        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.horde).exists())
        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.commonwealth).exists())
        self.assertEqual(BattleOrganization.objects.count(), 3)

        self.assertTrue(
            BattleOrganization.objects.get(organization=self.kingdom).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )
        self.assertTrue(
            BattleOrganization.objects.get(
                organization=self.commonwealth).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )

        self.assertTrue(BattleCharacter.objects.exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.kingdom,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.horde,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.commonwealth,
        ).exists())
        self.assertEqual(BattleCharacter.objects.count(), 3)

        self.assertTrue(BattleUnit.objects.exists())
        self.assertFalse(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_commonwealth,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior2,
                                      starting_manpower=60).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_kingdom,
                                      starting_manpower=100).exists()
        )
        self.assertEqual(BattleUnit.objects.count(), 3)

        response = self.client.get(self.battle.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)

        start_battle(self.battle)
        battle_tick(self.battle)

        self.unit_of_warrior.location_id = 1007
        self.unit_of_warrior.save()

        worldwide_battle_joins(world)
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior,
                                      starting_manpower=30).exists()
        )
        battle_tick(self.battle)

    def test_battle_create_from_units_with_allies_joining_during_battle2(self):
        self.unit_of_commonwealth.location_id = 1001
        self.unit_of_commonwealth.save()

        world = World.objects.get(id=2)
        worldwide_trigger_battles(world)

        self.assertTrue(Battle.objects.exists())

        self.battle = Battle.objects.get(id=1)

        self.assertEqual(self.battle.battleside_set.count(), 2)

        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.kingdom).exists())
        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.horde).exists())
        self.assertFalse(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.commonwealth).exists())
        self.assertEqual(BattleOrganization.objects.count(), 2)

        self.assertEqual(
            self.unit_of_commonwealth.owner_character.get_battle_participating_in(),
            None
        )

        self.assertTrue(
            BattleOrganization.objects.get(organization=self.kingdom).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )

        self.assertTrue(BattleCharacter.objects.exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.kingdom,
        ).exists())
        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.horde,
        ).exists())
        self.assertFalse(BattleCharacter.objects.filter(
            battle_organization__organization=self.commonwealth,
        ).exists())
        self.assertEqual(BattleCharacter.objects.count(), 2)

        self.assertTrue(BattleUnit.objects.exists())
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior,
                                      starting_manpower=30).exists()
        )
        self.assertFalse(
            BattleUnit.objects.filter(world_unit=self.unit_of_commonwealth,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior2,
                                      starting_manpower=60).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_kingdom,
                                      starting_manpower=100).exists()
        )
        self.assertEqual(BattleUnit.objects.count(), 3)

        response = self.client.get(self.battle.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)

        start_battle(self.battle)
        battle_tick(self.battle)

        self.unit_of_commonwealth.location_id = 1007
        self.unit_of_commonwealth.save()

        worldwide_battle_joins(world)

        self.assertTrue(
            BattleOrganization.objects.filter(side__battle=self.battle,
                                              organization=self.commonwealth).exists())
        self.assertEqual(BattleOrganization.objects.count(), 3)

        self.assertTrue(
            BattleOrganization.objects.get(organization=self.commonwealth).side.z !=
            BattleOrganization.objects.get(organization=self.horde).side.z
        )

        self.assertTrue(BattleCharacter.objects.filter(
            battle_organization__organization=self.commonwealth,
        ).exists())
        self.assertEqual(BattleCharacter.objects.count(), 3)

        self.assertTrue(BattleUnit.objects.exists())
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_commonwealth,
                                      starting_manpower=30).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_warrior2,
                                      starting_manpower=60).exists()
        )
        self.assertTrue(
            BattleUnit.objects.filter(world_unit=self.unit_of_kingdom,
                                      starting_manpower=100).exists()
        )
        self.assertEqual(BattleUnit.objects.count(), 4)

        self.assertEqual(
            self.unit_of_commonwealth.owner_character.get_battle_participating_in(),
            self.battle
        )

        battle_tick(self.battle)
