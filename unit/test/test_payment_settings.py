from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from character.models import Character
from unit.models import WorldUnit
from world.initialization import initialize_unit


class TestPaymentSettings(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)

        self.active_character = Character.objects.get(id=6)

        self.client.get(
            reverse(
                'character:activate',
                kwargs={'char_id': self.active_character.id}
            ),
            follow=True
        )

        self.not_my_unit = WorldUnit.objects.get(id=1)
        self.my_unit = WorldUnit.objects.get(id=2)
        initialize_unit(self.my_unit)
        initialize_unit(self.not_my_unit)

    def test_change_my_unit_payment_settings(self):
        self.assertFalse(self.my_unit.auto_pay)

        response = self.client.post(
            reverse('unit:payment_settings', kwargs={'unit_id': self.my_unit.id}),
            data={'action': 'enable'}
        )

        self.assertRedirects(
            response,
            self.my_unit.get_absolute_url()
        )
        self.my_unit.refresh_from_db()
        self.assertTrue(self.my_unit.auto_pay)

        response = self.client.post(
            reverse('unit:payment_settings', kwargs={'unit_id': self.my_unit.id}),
            data={'action': 'disable'}
        )

        self.assertRedirects(
            response,
            self.my_unit.get_absolute_url()
        )
        self.my_unit.refresh_from_db()
        self.assertFalse(self.my_unit.auto_pay)

    def test_not_my_unit_payment_settings(self):
        self.assertFalse(self.not_my_unit.auto_pay)

        response = self.client.post(
            reverse('unit:payment_settings', kwargs={'unit_id': self.not_my_unit.id}),
            data={'action': 'enable'}
        )

        self.assertEquals(
            response.status_code,
            404
        )
        self.not_my_unit.refresh_from_db()
        self.assertFalse(self.not_my_unit.auto_pay)
