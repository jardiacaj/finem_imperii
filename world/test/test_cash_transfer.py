from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from world.models import Character


class TestCashTransfer(TestCase):
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

    def test_can_transfer_cash_to_character_in_same_settlement(self):
        from_character = Character.objects.get(id=1)
        to_character = Character.objects.get(id=2)

        self.assertEqual(from_character.location.id, to_character.location.id)

        from_character_cash_before_transfer = from_character.cash
        to_character_cash_before_transfer = to_character.cash

        response = self.client.post(
            reverse('world:transfer_cash'),
            data={
                'from_character_id': from_character.id,
                'to_character_id': to_character.id,
                'transfer_cash_amount': 100,
            },
            follow=True
        )

        from_character.refresh_from_db()
        to_character.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertEqual(from_character_cash_before_transfer - 100, from_character.cash)
        self.assertEqual(to_character_cash_before_transfer + 100, to_character.cash)

    def test_cannot_transfer_cash_to_character_in_different_settlement(self):
        from_character = Character.objects.get(id=1)
        to_character = Character.objects.get(id=3)

        self.assertNotEqual(from_character.location.id, to_character.location.id)

        from_character_cash_before_transfer = from_character.cash
        to_character_cash_before_transfer = to_character.cash

        response = self.client.post(
            reverse('world:transfer_cash'),
            data={
                'from_character_id': from_character.id,
                'to_character_id': to_character.id,
                'transfer_cash_amount': 100,
            },
            follow=True
        )

        from_character.refresh_from_db()
        to_character.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertEqual(from_character_cash_before_transfer, from_character.cash)
        self.assertEqual(to_character_cash_before_transfer, to_character.cash)

    def test_cannot_transfer_more_cash_than_available(self):
        from_character = Character.objects.get(id=1)
        to_character = Character.objects.get(id=2)

        self.assertEqual(from_character.location.id, to_character.location.id)

        from_character_cash_before_transfer = from_character.cash
        to_character_cash_before_transfer = to_character.cash

        response = self.client.post(
            reverse('world:transfer_cash'),
            data={
                'from_character_id': from_character.id,
                'to_character_id': to_character.id,
                'transfer_cash_amount': 1000000000000,
            },
            follow=True
        )

        from_character.refresh_from_db()
        to_character.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('account:home')
        )

        self.assertEqual(from_character_cash_before_transfer, from_character.cash)
        self.assertEqual(to_character_cash_before_transfer, to_character.cash)
