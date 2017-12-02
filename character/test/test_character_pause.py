from datetime import timedelta

from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from character.models import Character
from turn.turn import TurnProcessor
from unit.models import WorldUnit


class TestCharacterPause(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        user.is_superuser = True
        user.save()
        self.assertEqual(User.objects.get(id=1), user)

    def test_pause_character(self):
        character = Character.objects.get(id=1)

        response = self.client.post(
            reverse('character:pause'),
            data={'character_id': character.id},
            follow=True
        )
        character.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertTrue(character.paused)

    def test_unit_of_pausing_character(self):
        character = Character.objects.get(id=2)
        unit = WorldUnit.objects.get(id=4)

        self.assertEqual(character.worldunit_set.all()[0], unit)

        response = self.client.post(
            reverse('character:pause'),
            data={'character_id': character.id},
            follow=True
        )
        character.refresh_from_db()
        unit.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertTrue(character.paused)
        self.assertFalse(character.worldunit_set.exists())
        self.assertEqual(unit.status, WorldUnit.NOT_MOBILIZED)
        self.assertIsNone(unit.location)
        self.assertIsNone(unit.owner_character)
        self.assertIsNone(unit.world)
        self.assertFalse(unit.soldier.exists())

    def test_unpause_character(self):
        character = Character.objects.get(id=1)

        response = self.client.post(
            reverse('character:pause'),
            data={'character_id': character.id},
            follow=True
        )
        character.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertTrue(character.paused)
        character.last_activation_time = timezone.now() - timedelta(days=30)
        character.save()

        response = self.client.post(
            reverse('character:unpause'),
            data={'character_id': character.id},
            follow=True
        )
        character.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertFalse(character.paused)
        self.assertEqual(character.get_violence_monopoly().name,
                         "Small Kingdom")

    def test_cant_unpause(self):
        character = Character.objects.get(id=1)
        self.assertTrue(character.can_pause())
        self.assertFalse(character.can_unpause())

        response = self.client.post(
            reverse('character:pause'),
            data={'character_id': character.id},
            follow=True
        )
        character.refresh_from_db()
        self.assertFalse(character.can_pause())
        self.assertFalse(character.can_unpause())

        character.last_activation_time = timezone.now() - timedelta(days=30)
        character.save()

        self.assertFalse(character.can_pause())
        self.assertTrue(character.can_unpause())

    def test_autopause(self):
        character = Character.objects.get(id=1)
        character.last_activation_time = timezone.now() - timedelta(days=30)
        character.save()
        turn_processor = TurnProcessor(character.world)
        turn_processor.character_pausing()
        character.refresh_from_db()
        self.assertTrue(character.paused)

    def test_do_not_autopause(self):
        character = Character.objects.get(id=1)
        character.last_activation_time = timezone.now()
        character.save()
        turn_processor = TurnProcessor(character.world)
        turn_processor.character_pausing()
        character.refresh_from_db()
        self.assertFalse(character.paused)
