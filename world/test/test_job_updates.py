from django.test import TestCase

from world.initialization import initialize_settlement
from world.models.buildings import Building
from world.models.geography import Settlement
from world.turn import TurnProcessor


class TestJobUpdates(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.settlement = Settlement.objects.get(name="Small Fynkah")

    def test_guild_default(self):
        initialize_settlement(self.settlement)
        turn_processor = TurnProcessor(self.settlement.tile.world)
        turn_processor.do_settlement_job_updates(self.settlement)
        self.assertEqual(
            self.settlement.guilds_setting, Settlement.GUILDS_KEEP)
        self.assertTrue(
            self.settlement.get_residents().filter(
                workplace__type=Building.GRAIN_FIELD).exists())
        self.assertFalse(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).exists())

    def test_guild_promote(self):
        self.settlement.guilds_setting = Settlement.GUILDS_PROMOTE
        self.settlement.save()
        initialize_settlement(self.settlement)
        turn_processor = TurnProcessor(self.settlement.tile.world)
        turn_processor.do_settlement_job_updates(self.settlement)
        self.assertTrue(
            self.settlement.get_residents().filter(
                workplace__type=Building.GRAIN_FIELD).exists())
        self.assertTrue(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).exists())
        self.assertEqual(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).count(), 10)

    def test_guild_prohibit(self):
        initialize_settlement(self.settlement)
        turn_processor = TurnProcessor(self.settlement.tile.world)
        turn_processor.do_settlement_job_updates(self.settlement)
        guild = self.settlement.building_set.get(type=Building.GUILD)
        for worker in list(self.settlement.get_residents().filter(
                workplace__type=Building.GRAIN_FIELD))[:30]:
            worker.workplace = guild
            worker.save()
        self.assertEqual(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).count(), 30)

        self.settlement.guilds_setting = Settlement.GUILDS_PROHIBIT
        self.settlement.save()
        turn_processor.do_settlement_job_updates(self.settlement)
        self.assertTrue(
            self.settlement.get_residents().filter(
                workplace__type=Building.GRAIN_FIELD).exists())
        self.assertFalse(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).exists())

    def test_guild_restrict(self):
        initialize_settlement(self.settlement)
        turn_processor = TurnProcessor(self.settlement.tile.world)
        turn_processor.do_settlement_job_updates(self.settlement)
        guild = self.settlement.building_set.get(type=Building.GUILD)
        for worker in list(self.settlement.get_residents().filter(
                workplace__type=Building.GRAIN_FIELD))[:30]:
            worker.workplace = guild
            worker.save()
        self.assertEqual(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).count(), 30)

        self.settlement.guilds_setting = Settlement.GUILDS_RESTRICT
        self.settlement.save()
        turn_processor.do_settlement_job_updates(self.settlement)
        self.assertTrue(
            self.settlement.get_residents().filter(
                workplace__type=Building.GRAIN_FIELD).exists())
        self.assertTrue(
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).exists())
        self.assertTrue(
            0 <
            self.settlement.get_residents().filter(
                workplace__type=Building.GUILD).count() <= 20)
