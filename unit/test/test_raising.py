from django.test import TestCase
from django.urls.base import reverse

import world.initialization
from unit.views.creation import test_if_hero_can_recruit_soldier_quantity, \
    RecruitmentFailure
from world.initialization import initialize_settlement
from world.models.npcs import NPC
from character.models import Character
from unit.models import WorldUnit


class TestRaising(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.character = Character.objects.get(id=1)
        self.character.cash = 100000
        self.character.save()
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse(
                'character:activate',
                kwargs={'char_id': self.character.id}
            ),
            follow=True
        )
        world.initialization.initialize_settlement(self.character.location)

    def test_rising_view(self):
        response = self.client.get(reverse('unit:raise'))
        self.assertEqual(response.status_code, 200)

    def test_default_raising(self):
        response = self.client.post(
            reverse('unit:raise'),
            data={
                "hours_invested": 300,
                "silver_invested": 100000,
                "unit_type": "infantry",
                "men": "on",
                "trained": "on",
                "untrained": "on",
                "skill_high": "on",
                "skill_medium": "on",
                "skill_low": "on",
                "age_middle": "on",
                "age_young": "on"
            },
            follow=True
        )

        unit = WorldUnit.objects.get(owner_character=self.character)
        self.assertRedirects(response, unit.get_absolute_url())

        self.assertEqual(unit.soldier.filter(male=True).exists(), True)
        self.assertEqual(unit.soldier.filter(male=False).exists(), False)
        self.assertEqual(
            unit.soldier.filter(age_months__gt=NPC.OLD_AGE_LIMIT).exists(),
            False)
        self.assertEqual(
            unit.soldier.filter(age_months__lt=NPC.YOUNG_AGE_LIMIT).exists(),
            False)

    def test_fail_because_not_enough_coins(self):
        self.character.cash = 0
        self.character.save()

        response = self.client.post(
            reverse('unit:raise'),
            data={
                "hours_invested": 300,
                "silver_invested": 100,
                "unit_type": "infantry",
                "men": "on",
                "trained": "on",
                "untrained": "on",
                "skill_high": "on",
                "skill_medium": "on",
                "skill_low": "on",
                "age_middle": "on",
                "age_young": "on"
            },
            follow=True
        )

        self.assertFalse(
            WorldUnit.objects.filter(owner_character=self.character).exists())
        self.assertRedirects(response, reverse('unit:raise'))

    def test_fail_because_no_gender_selected(self):
        response = self.client.post(
            reverse('unit:raise'),
            data={
                "hours_invested": 300,
                "silver_invested": 100,
                "unit_type": "infantry",
                "trained": "on",
                "untrained": "on",
                "skill_high": "on",
                "skill_medium": "on",
                "skill_low": "on",
                "age_middle": "on",
                "age_young": "on"
            },
            follow=True
        )

        self.assertRedirects(response, reverse('unit:raise'))
        self.assertFalse(
            WorldUnit.objects.filter(owner_character=self.character).exists())
