from unittest.case import skip

from django.test import TestCase

from organization.models.organization import Organization
from character.models import Character
from world.models.buildings import Building
from world.models.geography import Settlement
from world.turn import TurnProcessor


class TestTaxation(TestCase):
    fixtures = ['simple_world']

    def test_tax_countdown(self):
        state = Organization.objects.get(name="Small Kingdom")
        state.tax_countdown = 7
        state.save()

        turn_processor = TurnProcessor(state.world)
        turn_processor.do_taxes()

        state.refresh_from_db()
        self.assertEqual(state.tax_countdown, 6)

    def test_basic_tax(self):
        settlement = Settlement.objects.get(name="Small Valley")
        guild = settlement.building_set.get(type=Building.GUILD)
        guild.field_production_counter = 100
        guild.save()

        turn_processor = TurnProcessor(settlement.tile.world)
        turn_processor.do_taxes()

        state = settlement.tile.controlled_by.get_violence_monopoly()
        self.assertEqual(state.tax_countdown, 6)

        char1 = Character.objects.get(id=4)
        self.assertEqual(char1.cash, 10000 + 100 * 6 / 2)
        char2 = Character.objects.get(id=8)
        self.assertEqual(char2.cash, 10000 + 100 * 6 / 2)
