from django.test import TestCase
from django.urls.base import reverse

import world.initialization
from unit.views.creation import test_if_hero_can_recruit_soldier_quantity, \
    RecruitmentFailure
from world.initialization import initialize_settlement
from world.models.npcs import NPC
from character.models import Character
from unit.models import WorldUnit


class TestRecruitment(TestCase):
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

    def test_recruitment_view(self):
        response = self.client.get(reverse('unit:recruit'))
        self.assertEqual(response.status_code, 200)

    def test_default_recruitment(self):
        response = self.client.post(
            reverse('unit:recruit'),
            data={
                "count": 30,
                "unit_type": "light infantry soldiers",
                "pay": 3,
                "men": "on",
                "trained": "on",
                "untrained": "on",
                "skill_high": "on",
                "skill_medium": "on",
                "skill_low": "on",
                "age_middle": "on",
                "age_young": "on",
                "recruitment_type": "conscripted"
            },
            follow=True
        )

        unit = WorldUnit.objects.get(owner_character=self.character)
        self.assertRedirects(response, unit.get_absolute_url())

        self.assertEqual(unit.soldier.count(), 30)
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
            reverse('unit:recruit'),
            data={
                "count": 30,
                "unit_type": "light infantry soldiers",
                "pay": 3,
                "men": "on",
                "trained": "on",
                "untrained": "on",
                "skill_high": "on",
                "skill_medium": "on",
                "skill_low": "on",
                "age_middle": "on",
                "age_young": "on",
                "recruitment_type": "conscripted"
            },
            follow=True
        )

        self.assertFalse(
            WorldUnit.objects.filter(owner_character=self.character).exists())
        self.assertRedirects(response, reverse('unit:recruit'))

    def test_fail_because_no_gender_selected(self):
        response = self.client.post(
            reverse('unit:recruit'),
            data={
                "count": 30,
                "unit_type": "light infantry soldiers",
                "pay": 3,
                "trained": "on",
                "untrained": "on",
                "skill_high": "on",
                "skill_medium": "on",
                "skill_low": "on",
                "age_middle": "on",
                "age_young": "on",
                "recruitment_type": "conscripted"
            },
            follow=True
        )

        self.assertRedirects(response, reverse('unit:recruit'))
        self.assertFalse(
            WorldUnit.objects.filter(owner_character=self.character).exists())

    def test_can_recruit_method(self):
        character = Character.objects.get(id=6)
        self.assertFalse(character.can_conscript_unit())

    def test_max_conscription(self):
        character = Character.objects.get(id=6)
        initialize_settlement(character.location)

        # Don't raise
        test_if_hero_can_recruit_soldier_quantity(
            character,
            character.max_amount_of_conscripted_soldiers()
        )

        # Raise
        self.assertRaises(
            RecruitmentFailure,
            test_if_hero_can_recruit_soldier_quantity(
                character,
                character.max_amount_of_conscripted_soldiers() + 1
            )
        )
