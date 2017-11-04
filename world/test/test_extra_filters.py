from django.test import TestCase

from world.templatetags import extra_filters


class TestExtraFilters(TestCase):
    def test_subtract1(self):
        self.assertEqual(extra_filters.subtract(1, 2), -1)

    def test_subtract2(self):
        self.assertEqual(extra_filters.subtract(100, 0), 100)

    def test_nice_turn1(self):
        self.assertEqual(extra_filters.nice_turn(0), "January 815 I.E.")

    def test_nice_turn2(self):
        self.assertEqual(extra_filters.nice_turn(25), "February 817 I.E.")

    def test_nice_hours1(self):
        self.assertEqual(extra_filters.nice_hours(25), "1 day and 1 hour")

    def test_nice_hours2(self):
        self.assertEqual(extra_filters.nice_hours(50), "2 days and 2 hours")

    def test_nice_turns1(self):
        self.assertEqual(extra_filters.nice_turns(25), "2 years and 1 month")

    def test_nice_turns2(self):
        self.assertEqual(extra_filters.nice_turns(0), "0 months")
