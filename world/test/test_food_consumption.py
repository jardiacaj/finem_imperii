import math
from django.test import TestCase

from world.initialization import initialize_settlement
from world.models import Building, NPC, Settlement, InventoryItem
from world.turn import TurnProcessor


class TestFieldProduction(TestCase):
    fixtures = ['simple_world']

    def test_food_consumption(self):
        settlement = Settlement.objects.get(name="Small Valley")
        settlement.population = 100
        granary = settlement.get_default_granary()
        bushels = granary.get_public_bushels_object()
        bushels.quantity = 200
        bushels.save()

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_settlement_food_consumption(settlement)

        bushels.refresh_from_db()
        self.assertEqual(bushels.quantity, 100)

    def test_hunger(self):
        settlement = Settlement.objects.get(name="Small Valley")
        settlement.population = 10
        granary = settlement.get_default_granary()
        bushels = granary.get_public_bushels_object()
        bushels.quantity = 9
        bushels.save()

        initialize_settlement(settlement)

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_settlement_food_consumption(settlement)

        bushels.refresh_from_db()
        self.assertEqual(bushels.quantity, 0)

        self.assertEqual(settlement.npc_set.filter(hunger__gt=0).count(), 1)

    def test_hunger2(self):
        settlement = Settlement.objects.get(name="Small Valley")
        settlement.population = 10
        granary = settlement.get_default_granary()
        bushels = granary.get_public_bushels_object()
        bushels.quantity = 3
        bushels.save()

        initialize_settlement(settlement)

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_settlement_food_consumption(settlement)

        bushels.refresh_from_db()
        self.assertEqual(bushels.quantity, 0)

        self.assertEqual(settlement.npc_set.filter(hunger__gt=0).count(), 7)
