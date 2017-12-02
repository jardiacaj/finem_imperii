import math

from django.test import TestCase

from turn.turn import TurnProcessor
from world.models.buildings import Building
from world.models.geography import Settlement
from world.models.items import InventoryItem
from world.models.npcs import NPC


class TestFieldProduction(TestCase):
    fixtures = ['simple_world']

    def test_field_input(self):
        settlement = Settlement.objects.get(name="Small Valley")
        buildings = Building.objects.get(
            type=Building.GRAIN_FIELD, settlement=settlement
        )

        for i in range(10):
            NPC.objects.create(
                name="foo",
                male=False,
                able=True,
                age_months=20*12,
                residence=None,
                origin=settlement,
                location=settlement,
                workplace=buildings,
                unit=None,
                trained_soldier=False,
                skill_fighting=0
            )

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(buildings)

        buildings.refresh_from_db()
        self.assertEqual(buildings.quantity, 3110)
        self.assertEqual(buildings.worker.count(), 10)
        self.assertEqual(
            buildings.field_production_counter,
            math.floor((10 / (3110 / 10)) * (1/10) * 1000)
        )

    def test_field_input_ideal_workload(self):
        settlement = Settlement.objects.get(name="Small Valley")
        buildings = Building.objects.get(
            type=Building.GRAIN_FIELD, settlement=settlement
        )
        buildings.quantity = 100
        buildings.save()

        for i in range(10):
            NPC.objects.create(
                name="foo",
                male=False,
                able=True,
                age_months=20*12,
                residence=None,
                origin=settlement,
                location=settlement,
                workplace=buildings,
                unit=None,
                trained_soldier=False,
                skill_fighting=0
            )

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(buildings)

        buildings.refresh_from_db()
        self.assertEqual(buildings.quantity, 100)
        self.assertEqual(buildings.worker.count(), 10)
        self.assertEqual(
            buildings.field_production_counter,
            100
        )

    def test_field_input_over_ideal_workload(self):
        settlement = Settlement.objects.get(name="Small Valley")
        buildings = Building.objects.get(
            type=Building.GRAIN_FIELD, settlement=settlement
        )
        buildings.quantity = 100
        buildings.save()

        for i in range(20):
            NPC.objects.create(
                name="foo",
                male=False,
                able=True,
                age_months=20*12,
                residence=None,
                origin=settlement,
                location=settlement,
                workplace=buildings,
                unit=None,
                trained_soldier=False,
                skill_fighting=0
            )

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(buildings)

        buildings.refresh_from_db()
        self.assertEqual(buildings.quantity, 100)
        self.assertEqual(buildings.worker.count(), 20)
        self.assertEqual(
            buildings.field_production_counter,
            112
        )

    def test_field_input_excessive_workload(self):
        settlement = Settlement.objects.get(name="Small Valley")
        buildings = Building.objects.get(
            type=Building.GRAIN_FIELD, settlement=settlement
        )
        buildings.quantity = 10
        buildings.save()

        for i in range(20):
            NPC.objects.create(
                name="foo",
                male=False,
                able=True,
                age_months=20*12,
                residence=None,
                origin=settlement,
                location=settlement,
                workplace=buildings,
                unit=None,
                trained_soldier=False,
                skill_fighting=0
            )

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(buildings)

        buildings.refresh_from_db()
        self.assertEqual(buildings.quantity, 10)
        self.assertEqual(buildings.worker.count(), 20)
        self.assertEqual(
            buildings.field_production_counter,
            150
        )

    def test_field_output_after_ideal_input(self):
        settlement = Settlement.objects.get(name="Small Valley")
        buildings = Building.objects.get(
            type=Building.GRAIN_FIELD, settlement=settlement
        )
        buildings.quantity = 100
        buildings.field_production_counter = 1000
        buildings.save()
        settlement.tile.world.current_turn = 6
        settlement.tile.world.save()

        for i in range(10):
            NPC.objects.create(
                name="foo",
                male=False,
                able=True,
                age_months=20*12,
                residence=None,
                origin=settlement,
                location=settlement,
                workplace=buildings,
                unit=None,
                trained_soldier=False,
                skill_fighting=0
            )

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(buildings)

        buildings.refresh_from_db()
        self.assertEqual(buildings.quantity, 100)
        self.assertEqual(buildings.worker.count(), 10)
        self.assertEqual(
            buildings.field_production_counter,
            math.floor(1000 * 6/7)
        )
        bushel_object = settlement.get_default_granary().inventoryitem_set.get(
            type=InventoryItem.GRAIN
        )
        self.assertEqual(bushel_object.quantity, math.floor(100 * 1/7 * 2.4))

    def test_reset_production(self):
        settlement = Settlement.objects.get(name="Small Valley")
        buildings = Building.objects.get(
            type=Building.GRAIN_FIELD, settlement=settlement
        )
        buildings.field_production_counter = 1000
        buildings.save()
        settlement.tile.world.current_turn = 8
        settlement.tile.world.save()

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(buildings)

        buildings.refresh_from_db()
        self.assertEqual(buildings.field_production_counter, 0)


class TestGuildProduction(TestCase):
    fixtures = ['simple_world']

    def test_guild_input(self):
        settlement = Settlement.objects.get(name="Small Valley")
        guild = Building.objects.get(
            type=Building.GUILD, settlement=settlement
        )

        for i in range(10):
            NPC.objects.create(
                name="foo",
                male=False,
                able=True,
                age_months=20*12,
                residence=None,
                origin=settlement,
                location=settlement,
                workplace=guild,
                unit=None,
                trained_soldier=False,
                skill_fighting=0
            )

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_building_production(guild)

        guild.refresh_from_db()
        self.assertEqual(guild.quantity, 1)
        self.assertEqual(guild.worker.count(), 10)
        self.assertEqual(guild.field_production_counter, 10)
