import math
from django.test import TestCase

from world.models import Building, NPC, Settlement
from world.turn import TurnProcessor


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
