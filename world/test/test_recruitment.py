from django.test import TestCase
from django.urls.base import reverse

import world.initialization
from world.models import WorldUnit, Character, NPC


class TestUnitActions(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.character = Character.objects.get(id=1)
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse(
                'world:activate_character',
                kwargs={'char_id': self.character.id}
            ),
            follow=True
        )
        world.initialization.initialize_settlement(self.character.location)

    def test_recruitment_view(self):
        response = self.client.get(reverse('world:recruit'))
        self.assertEqual(response.status_code, 200)

    def test_default_recruitment(self):
        response = self.client.post(
            reverse('world:recruit'),
            data={
                "conscript_count": 30,
                "conscript_unit_type": "infantry",
                "conscript_pay": 3,
                "conscript_men": "on",
                "conscript_trained": "on",
                "conscript_untrained": "on",
                "conscript_skill_high": "on",
                "conscript_skill_medium": "on",
                "conscript_skill_low": "on",
                "conscript_age_middle": "on",
                "conscript_age_young": "on",
                "recruitment_type": "conscription"
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

    def test_fail_because_no_gender_selected(self):
        response = self.client.post(
            reverse('world:recruit'),
            data={
                "conscript_count": 30,
                "conscript_unit_type": "infantry",
                "conscript_pay": 3,
                "conscript_trained": "on",
                "conscript_untrained": "on",
                "conscript_skill_high": "on",
                "conscript_skill_medium": "on",
                "conscript_skill_low": "on",
                "conscript_age_middle": "on",
                "conscript_age_young": "on",
                "recruitment_type": "conscription"
            },
            follow=True
        )

        self.assertRedirects(response, reverse('world:recruit'))
        self.assertFalse(
            WorldUnit.objects.filter(owner_character=self.character).exists())
