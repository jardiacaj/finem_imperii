from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from character.models import Character
from unit.models import WorldUnit
from world.initialization import initialize_unit


class TestDebtPayment(TestCase):
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

    def test_pay_my_units_debt(self):
        cash_before = self.active_character.cash
        self.my_unit.owners_debt = 100
        self.my_unit.save()

        response = self.client.post(
            reverse('unit:pay_debt', kwargs={'unit_id': self.my_unit.id}),
            data={'amount': 100}
        )

        self.assertRedirects(
            response,
            self.my_unit.get_absolute_url()
        )
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.owners_debt, 0)
        self.active_character.refresh_from_db()
        self.assertEqual(self.active_character.cash, cash_before - 100)

    def test_pay_more_than_my_units_debt(self):
        cash_before = self.active_character.cash
        self.my_unit.owners_debt = 50
        self.my_unit.save()

        response = self.client.post(
            reverse('unit:pay_debt', kwargs={'unit_id': self.my_unit.id}),
            data={'amount': 100}
        )

        self.assertRedirects(
            response,
            self.my_unit.get_absolute_url()
        )
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.owners_debt, 0)
        self.active_character.refresh_from_db()
        self.assertEqual(self.active_character.cash, cash_before - 50)

    def test_pay_not_my_units_debt(self):
        cash_before = self.active_character.cash
        self.not_my_unit.owners_debt = 50
        self.not_my_unit.save()

        response = self.client.post(
            reverse('unit:pay_debt', kwargs={'unit_id': self.not_my_unit.id}),
            data={'amount': 100}
        )

        self.assertRedirects(
            response,
            self.not_my_unit.get_absolute_url()
        )
        self.not_my_unit.refresh_from_db()
        self.assertEqual(self.not_my_unit.owners_debt, 0)
        self.active_character.refresh_from_db()
        self.assertEqual(self.active_character.cash, cash_before - 50)
