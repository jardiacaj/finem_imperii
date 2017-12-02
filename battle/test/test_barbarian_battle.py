from django.test import TestCase
from django.urls.base import reverse

from battle.battle_init import start_battle
from battle.battle_tick import battle_tick
from battle.models import Battle, BattleUnit, Order, BattleOrganization, \
    BattleCharacter, BattleSoldier, BattleSoldierInTurn
from turn.battle import trigger_battles_in_tile
from unit.models import WorldUnit
from world.initialization import initialize_unit
from world.models.geography import Tile, World


class TestBarbarianBattle(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 7}),
            follow=True
        )

    def test_battle_initialization(self):
        self.my_unit = WorldUnit.objects.create(
            owner_character_id=7,
            world_id=2,
            location_id=1003,
            origin_id=1003,
            name="Commonwealth lord unit",
            recruitment_type=WorldUnit.CONSCRIPTION,
            type=WorldUnit.INFANTRY,
            status=WorldUnit.FOLLOWING,
            mobilization_status_since=0,
            current_status_since=0,
            generation_size=5,
            default_battle_orders=Order.objects.create(what=Order.CHARGE)
        )

        self.barbarian_unit = WorldUnit.objects.create(
            owner_character=None,
            world_id=2,
            location_id=1003,
            origin_id=1003,
            name="Barbarian unit",
            recruitment_type=WorldUnit.CONSCRIPTION,
            type=WorldUnit.INFANTRY,
            status=WorldUnit.FOLLOWING,
            mobilization_status_since=0,
            current_status_since=0,
            generation_size=30,
            default_battle_orders=Order.objects.create(what=Order.MOVE)
        )

        initialize_unit(self.my_unit)
        initialize_unit(self.barbarian_unit)
        self.tile = Tile.objects.get(id=105)
        trigger_battles_in_tile(self.tile)
        self.battle = Battle.objects.get(id=1)

        self.assertTrue(
            WorldUnit.objects.filter(owner_character__isnull=True).exists())
        start_battle(self.battle)

        self.assertTrue(
            BattleOrganization.objects.filter(
                organization=World.objects.get(id=2).get_barbaric_state()
            ).exists()
        )

        self.assertTrue(
            BattleOrganization.objects.filter(
                organization_id=105
            ).exists()
        )

        self.assertEqual(BattleCharacter.objects.count(), 1)

        self.assertEqual(BattleUnit.objects.count(), 2)
        self.assertEqual(
            BattleUnit.objects.filter(battle_side__battle=self.battle).count(),
            2)

        self.assertEqual(
            BattleSoldier.objects.filter(battle_contubernium__battle_unit__battle_side__battle=self.battle).count(),
            35
        )

        self.assertEqual(
            BattleSoldierInTurn.objects.filter(battle_turn__battle=self.battle).count(),
            35
        )

    def test_battle_orders_flee(self):
        self.my_unit = WorldUnit.objects.create(
            owner_character_id=7,
            world_id=2,
            location_id=1003,
            origin_id=1003,
            name="Commonwealth lord unit",
            recruitment_type=WorldUnit.CONSCRIPTION,
            type=WorldUnit.INFANTRY,
            status=WorldUnit.FOLLOWING,
            mobilization_status_since=0,
            current_status_since=0,
            generation_size=30,
            default_battle_orders=Order.objects.create(what=Order.CHARGE)
        )

        self.barbarian_unit = WorldUnit.objects.create(
            owner_character=None,
            world_id=2,
            location_id=1003,
            origin_id=1003,
            name="Barbarian unit",
            recruitment_type=WorldUnit.CONSCRIPTION,
            type=WorldUnit.INFANTRY,
            status=WorldUnit.FOLLOWING,
            mobilization_status_since=0,
            current_status_since=0,
            generation_size=5,
            default_battle_orders=Order.objects.create(what=Order.MOVE)
        )

        initialize_unit(self.my_unit)
        initialize_unit(self.barbarian_unit)
        self.tile = Tile.objects.get(id=105)
        trigger_battles_in_tile(self.tile)
        self.battle = Battle.objects.get(id=1)

        self.assertTrue(
            WorldUnit.objects.filter(owner_character__isnull=True).exists())
        start_battle(self.battle)

        battle_unit = BattleUnit.objects.get(owner=None)
        self.assertEqual(
            battle_unit.get_order().what, Order.FLEE)

        battle_tick(self.battle)

        battle_unit = BattleUnit.objects.get(owner=None)
        self.assertEqual(
            battle_unit.get_order().what, Order.FLEE)

    def test_battle_orders_attack(self):
        self.my_unit = WorldUnit.objects.create(
            owner_character_id=7,
            world_id=2,
            location_id=1003,
            origin_id=1003,
            name="Commonwealth lord unit",
            recruitment_type=WorldUnit.CONSCRIPTION,
            type=WorldUnit.INFANTRY,
            status=WorldUnit.FOLLOWING,
            mobilization_status_since=0,
            current_status_since=0,
            generation_size=5,
            default_battle_orders=Order.objects.create(what=Order.CHARGE)
        )

        self.barbarian_unit = WorldUnit.objects.create(
            owner_character=None,
            world_id=2,
            location_id=1003,
            origin_id=1003,
            name="Barbarian unit",
            recruitment_type=WorldUnit.CONSCRIPTION,
            type=WorldUnit.INFANTRY,
            status=WorldUnit.FOLLOWING,
            mobilization_status_since=0,
            current_status_since=0,
            generation_size=30,
            default_battle_orders=Order.objects.create(what=Order.MOVE)
        )

        initialize_unit(self.my_unit)
        initialize_unit(self.barbarian_unit)
        self.tile = Tile.objects.get(id=105)
        trigger_battles_in_tile(self.tile)
        self.battle = Battle.objects.get(id=1)

        self.assertTrue(
            WorldUnit.objects.filter(owner_character__isnull=True).exists())
        start_battle(self.battle)

        battle_unit = BattleUnit.objects.get(owner=None)
        self.assertEqual(
            battle_unit.get_order().what, Order.ADVANCE_IN_FORMATION)

        battle_tick(self.battle)

        battle_unit = BattleUnit.objects.get(owner=None)
        self.assertEqual(
            battle_unit.get_order().what, Order.ADVANCE_IN_FORMATION)
